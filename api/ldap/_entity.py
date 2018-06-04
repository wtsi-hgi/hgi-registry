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

from common import types as T
from . import _types as ldapT
from ._exceptions import *
from ._server import Server
from ._scope import Scope


class Entity(ldapT.Payload):
    """ Generic LDAP entity model """
    _server:T.Optional[Server]
    _dn:str
    _payload:T.Optional[T.Dict[str, ldapT.Data]]

    def __init__(self, dn:str) -> None:
        self._server = None
        self._dn = dn
        self._payload = None

    @property
    def dn(self) -> str:
        return self._dn

    def _inject_server(self, server:Server) -> None:
        # NOTE Server dependency injection is delegated to a setter,
        # rather than a constructor argument, as it's not the entity's
        # responsibility to re-establish a connection if/when it dies
        self._server = server

    server = property(None, _inject_server)

    def __repr__(self) -> str:
        return f"<Entity {self.dn}>"

    def __getitem__(self, item:str) -> ldapT.Data:
        if self._payload is None:
            raise PayloadNotFetched(f"Data for {self._dn} has not been fetched!")

        return self._payload[item]

    def __iter__(self) -> T.Iterable[str]:
        if self._payload is None:
            raise PayloadNotFetched(f"Data for {self._dn} has not been fetched!")

        return iter(self._payload.keys())

    def __len__(self) -> int:
        if self._payload is None:
            raise PayloadNotFetched(f"Data for {self._dn} has not been fetched!")

        return len(self._payload)

    async def fetch(self, *attrs:str) -> None:
        """ Fetch LDAP entry attributes """
        if self._server is None:
            raise NoServerSpecified("No LDAP server specified!")

        to_fetch = list(attrs) if attrs else None
        exists = False
        async for _, payload in self._server.search(self._dn, Scope.Base, attrs=to_fetch):
            exists = True
            self._payload = {**(self._payload or {}), **payload}

        if not exists:
            raise NoSuchDistinguishedName(f"{self._dn} does not exist!")


def entity_adaptor_factory(server:Server) -> T.Callable:
    """ Factory that creates an Entity adaptor for search results """
    def _adaptor(result:T.Tuple[str, ldapT.Payload]) -> Entity:
        """ Adapt results from Server.search into Entity instances """
        dn, payload = result

        entity = Entity(dn)
        entity._payload = payload
        entity._server = server

        return entity

    return _adaptor
