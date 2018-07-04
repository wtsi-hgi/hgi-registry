"""
Copyright (c) 2018 Genome Research Ltd.

Author: Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from abc import ABCMeta
from asyncio import Lock
from collections import defaultdict
import re

from api import ldap
from common import types as T, time
from common.logging import Level, log
from ._mixins import Expirable, Serialisable, Hypermedia
from ._adaptors import Attribute


class BaseNode(Expirable, Serialisable, Hypermedia, metaclass=ABCMeta):
    """ Base class for specific LDAP objects """
    _rdn_attr:T.ClassVar[str]
    _base_dn:T.ClassVar[str]
    _object_classes:T.ClassVar[T.List[str]]

    _identity:str
    _entity:ldap.Entity
    _attr_map:T.Dict[str, Attribute]

    _update_lock:Lock

    def __init__(self, identity:str, server:ldap.Server, attr_map:T.Dict[str, Attribute], shelf_life:T.TimeDelta) -> None:
        super().__init__(shelf_life)

        self._identity = identity
        self._entity = ldap.Entity(self.dn)
        self._entity.server = server

        self._attr_map = attr_map

        self._update_lock = Lock()

    def __getattr__(self, attr:str) -> T.Any:
        if attr not in self._attr_map:
            raise AttributeError(f"No such attribute {attr}!")

        return self._attr_map[attr](self._entity)

    async def __updator__(self) -> None:
        async with self._update_lock:
            log(f"Updating {self.identity}", Level.Debug)
            await self._entity.fetch()

    @classmethod
    def extract_rdn(cls, dn:str) -> str:
        """ Extract the RDN from the DN """
        search = re.search(fr"(?<=^{cls._rdn_attr}=).+(?=,{cls._base_dn}$)", dn)
        if not search:
            raise ldap.NoSuchDistinguishedName(f"Cannot extract {cls.__name__} RDN from {dn}")

        return search[0]

    @classmethod
    def build_dn(cls, identity:str) -> str:
        return f"{cls._rdn_attr}={ldap.escape(identity)},{cls._base_dn}"

    @property
    def dn(self) -> str:
        return self.build_dn(self.identity)

    @property
    def identity(self) -> str:
        return self._identity

    def reattach_server(self, server:ldap.Server) -> None:
        """
        Reattach an LDAP server to the node's entity, in the event of
        connection problems and forcibly expire the node
        """
        log(f"Attaching {self.identity} to {server.uri}", Level.Debug)
        self._entity.server = server
        self.expire()


class NoMatches(BaseException):
    """ Raised when trying to seed the registry with no data """

class BaseRegistry(Expirable, Serialisable, T.Container[BaseNode], metaclass=ABCMeta):
    """ Base container class for nodes """
    _server:ldap.Server
    _registry:T.Dict[str, BaseNode]

    _seed_lock:T.DefaultDict[T.Type[BaseNode], Lock]

    def __init__(self, server:ldap.Server, shelf_life:T.TimeDelta) -> None:
        self._server = server
        self._registry = {}

        # Create seeding lock for the given class, if it doesn't exist.
        # We reasonably assume that the data fetched for each node class
        # is mutually exclusive.
        self._seed_lock = defaultdict(Lock)

        super().__init__(shelf_life)

    def __contains__(self, dn:str) -> bool:
        return dn in self._registry

    @property
    def server(self) -> ldap.Server:
        return self._server

    @server.setter
    def server(self, server:ldap.Server) -> None:
        """
        Reattach an LDAP server to every node, in the event of
        connection problems and forcibly expire the registry
        """
        log(f"Reattaching all nodes to {server.uri}", Level.Debug)
        self._server = server
        self.expire()
        for node in self._registry:
            self._registry[node].reattach_server(server)

    async def seed(self, cls:T.Type[BaseNode], search:T.Optional[str] = None) -> None:
        """
        Seed the registry with nodes of the specified type as returned
        by the given search term. Note that the search term is assumed
        to be hygienic; it's the caller's responsibility to ensure
        inputs are escaped to avoid injection attacks.
        """
        def _adaptor(result) -> T.Tuple[str, BaseNode]:
            dn, payload = result
            identity = cls.extract_rdn(dn)
            node = cls(identity, self)
            node._entity._payload = payload
            node._last_updated = time.now()
            return dn, node

        # Build the conjunctive search term from the class' object
        # classes and the sanitised search term, if provided
        conjunction = "(&" \
                    + "".join(f"(objectClass={ldap.escape(oc)})" for oc in cls._object_classes) \
                    + (search or "") \
                    + ")"

        found = False
        log(f"Seeding registry with {cls.__name__} results from {conjunction}...", Level.Debug)

        async with self._seed_lock[cls]:
            async for dn, node in self._server.search(cls._base_dn, ldap.Scope.OneLevel, conjunction, adaptor=_adaptor):
                self._registry[dn] = node
                found = True

        if not found:
            raise NoMatches(f"No matches found for {conjunction} under {cls._base_dn} to seed registry")

    async def get(self, cls:T.Type[BaseNode], identity:str) -> BaseNode:
        """
        Get a node from the registry of the specified type, seeding the
        registry if the node doesn't exist, and updating it if necessary
        """
        dn = cls.build_dn(identity)
        if dn not in self._registry:
            search = f"({cls._rdn_attr}={ldap.escape(identity)})"
            await self.seed(cls, search)

        node = self._registry[dn]
        if node.has_expired:
            await node.update()

        return node

    def keys(self, cls:T.Type[BaseNode]) -> T.Iterator[str]:
        """ Generator of all nodes matching the specified type """
        for k in self._registry:
            try:
                identity = cls.extract_rdn(k)
                yield identity

            except ldap.NoSuchDistinguishedName:
                pass
