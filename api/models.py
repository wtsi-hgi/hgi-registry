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

from abc import ABCMeta, abstractmethod
import base64
import re

from common import types as T, time
from . import ldap


__all__ = ["Registry", "Person", "Group"]


class _Expirable(metaclass=ABCMeta):
    """ Base class for items that ought to be periodically updated """
    _last_updated:T.Optional[T.DateTime]
    _shelf_life:T.TimeDelta

    def __init__(self, shelf_life:T.TimeDelta) -> None:
        self._last_updated = None
        self._shelf_life = shelf_life

    @abstractmethod
    async def __updator__(self, *args, **kwargs) -> None:
        """ Update the object's state """

    @property
    def has_expired(self) -> bool:
        """ Has our entity expired? """
        if self._last_updated is None:
            return True

        age = time.now() - self._last_updated
        return age > self._shelf_life

    async def update(self, *args, **kwargs) -> None:
        self._last_updated = time.now()
        await self.__updator__(*args, **kwargs)


_AttrAdaptorT = T.Callable[[T.List[T.Union[T.Text, T.ByteString]]], T.Any]

_flatten = lambda x: x[0].decode()  # Adaptor to flatten simple text attributes

def _to_bool(x) -> bool:
    """ Adaptor to convert common strings to Booleans """
    value = _flatten(x).upper()
    return value in ["TRUE", "YES"]

class _Attribute(object):
    """ Potentially optional attribute, with an adaptor to munge data """
    # TODO Allow multiple input attributes for mapping
    _dn:str
    _adaptor:_AttrAdaptorT
    _optional:bool
    _default:T.Any

    def __init__(self, dn:str, *, adaptor:_AttrAdaptorT = _flatten, optional:bool = False, default:T.Any = None) -> None:
        self._dn = dn
        self._adaptor = adaptor
        self._optional = optional
        self._default = default

    def __call__(self, entity:ldap.Entity) -> T.Any:
        try:
            return self._adaptor(entity[self._dn])

        except KeyError:
            if self._optional:
                return self._default

            raise

class _Node(_Expirable):
    """ Superclass for specific LDAP object classes """
    _rdn_attr:T.ClassVar[str]
    _base_dn:T.ClassVar[str]

    _identity:str
    _entity:ldap.Entity
    _attr_map:T.Dict[str, T.Tuple[str, _AttrAdaptorT]]

    def __init__(self, identity:str, server:ldap.Server, attr_map:T.Dict[str, _Attribute], shelf_life:T.TimeDelta) -> None:
        super().__init__(shelf_life)

        self._identity = identity
        self._entity = ldap.Entity(self.dn)
        self._entity.server = server

        self._attr_map = attr_map

    def __getattr__(self, attr:str) -> str:
        if attr not in self._attr_map:
            raise AttributeError(f"No such attribute {attr}!")

        return self._attr_map[attr](self._entity)

    async def __updator__(self, *_, **__) -> None:
        await self._entity.fetch()

    @classmethod
    def extract_rdn(cls, dn:str) -> str:
        """ Extract the RDN from the DN """
        search = re.search(fr"(?<=^{cls._rdn_attr}=).*(?=,{cls._base_dn}$)", dn)
        if not search:
            raise ldap.NoSuchDistinguishedName(f"Cannot extract {cls.__name__} RDN from {dn}")

        return search[0]

    @classmethod
    def build_dn(cls, identity:str) -> str:
        return f"{cls._rdn_attr}={identity},{cls._base_dn}"

    @property
    def dn(self) -> str:
        return self.__class__.build_dn(self._identity)

    def reattach_server(self, server:ldap.Server) -> None:
        """
        Reattach an LDAP server to the node's entity, in the event of
        connection problems
        """
        self._entity.server = server


class Registry(T.Container[_Node]):
    """ Container for nodes """
    _server:ldap.Server
    _shelf_life:T.TimeDelta
    _registry:T.Dict[str, _Node]

    def __init__(self, server:ldap.Server, shelf_life:T.TimeDelta) -> None:
        self._server = server
        self._shelf_life = shelf_life
        self._registry = {}

    def __contains__(self, dn:str) -> bool:
        return dn in self._registry

    @property
    def server(self) -> ldap.Server:
        return self._server

    @server.setter
    def server(self, server:ldap.Server) -> None:
        """
        Reattach an LDAP server to every node, in the event of
        connection problems
        """
        self._server = server
        for node in self._registry:
            self._registry[node].reattach_server(server)

    @property
    def shelf_life(self) -> T.TimeDelta:
        return self._shelf_life

    async def seed(self, cls:T.Type[_Node], search:str) -> None:
        """
        Seed the registry with nodes of the specified type as returned
        by the given search term
        """
        def _adaptor(result) -> T.Tuple[str, _Node]:
            # FIXME Injection attack site
            dn, payload = result
            identity = cls.extract_rdn(dn)
            node = cls(identity, self)
            node._entity._payload = payload
            node._last_updated = time.now()
            return dn, node

        async for dn, node in self._server.search(cls._base_dn, ldap.Scope.OneLevel, search, adaptor=_adaptor):
            self._registry[dn] = node

    async def get(self, cls:T.Type[_Node], identity:str) -> _Node:
        """
        Get a node from the registry of the specified type, seeding the
        registry if the node doesn't exist, and updating it if necessary
        """
        dn = cls.build_dn(identity)
        if dn not in self._registry:
            # FIXME Injection attack site
            search = f"({cls._rdn_attr}={identity})"
            await self.seed(cls, search)

        node = self._registry[dn]
        if node.has_expired:
            await node.update()

        return node

    def keys(self, cls:T.Type[_Node]) -> T.Iterator[str]:
        """ Generator of all nodes matching the specified type """
        for k in self._registry:
            try:
                identity = cls.extract_rdn(k)
                yield identity

            except ldap.NoSuchDistinguishedName:
                pass


class Person(_Node):
    """ High level LDAP person model """
    _rdn_attr = "uid"
    _base_dn = "ou=people,dc=sanger,dc=ac,dc=uk"

    @staticmethod
    def decode_photo(payload) -> bytes:
        """ Adaptor that returns the decoded JPEG data """
        # FIXME Return an async generator instead? Is that overkill?
        jpeg, *_ = map(base64.b64decode, payload)
        return jpeg

    def __init__(self, uid:str, registry:Registry) -> None:
        attr_map = {
            "name":  _Attribute("cn"),
            "mail":  _Attribute("mail"),
            "title": _Attribute("title", optional=True),
            "photo": _Attribute("jpegPhoto", adaptor=Person.decode_photo, optional=True)
            # Real person? Active account?...
        }

        super().__init__(uid, registry.server, attr_map, registry.shelf_life)


class Group(_Node):
    """ High level LDAP group model """
    _rdn_attr = "cn"
    _base_dn = "ou=group,dc=sanger,dc=ac,dc=uk"

    _registry:Registry

    def _resolve_dn(self, dn:str) -> Person:
        # FIXME This should return a coroutine that fetches the person
        rdn = Person.extract_rdn(dn)
        return Person(rdn, self._registry)

    def resolve_person(self, payload) -> Person:
        return self._resolve_dn(_flatten(payload))

    def resolve_people(self, payload) -> T.Iterator[Person]:
        return map(self._resolve_dn, payload)

    def __init__(self, cn:str, registry:Registry) -> None:
        attr_map = {
            "name":        _Attribute("cn"),
            "active":      _Attribute("sangerHumgenProjectActive", adaptor=_to_bool),
            "pi":          _Attribute("sangerProjectPI", adaptor=self.resolve_person),
            "owners":      _Attribute("owner", adaptor=self.resolve_people),
            "members":     _Attribute("member", adaptor=self.resolve_people),
            "description": _Attribute("description", optional=True),
            "prelims":     _Attribute("sangerPrelimID", optional=True, default=[])
            # sangerHumgenDataSecurityLevel
            # sangerHumgenProjectStorageResources
            # sangerHumgenProjectStorageQuotas
        }

        self._registry = registry
        super().__init__(cn, registry.server, attr_map, registry.shelf_life)
