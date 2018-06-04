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

import ldap
from ldap.ldapobject import LDAPObject
from ldap.resiter import ResultProcessor

from common import types as T
from . import _types as ldapT
from ._exceptions import *
from ._scope import Scope


_ResultT = T.Tuple[str, ldapT.Payload]  # DN: Payload

class _SearchResults(T.AsyncIterator[_ResultT]):
    """ Asynchronous generator from LDAP search generator """
    def __init__(self, results) -> None:
        self._results = results

    def __aiter__(self):
        return self

    async def __anext__(self) -> _ResultT:
        """ Iterate through generator """
        try:
            _, [(dn, entry)], _, _ = next(self._results)

        except StopIteration:
            raise StopAsyncIteration

        return dn, entry


_AdaptedT = T.TypeVar("_AdaptedT")
_AdaptorT = T.Callable[[_ResultT], _AdaptedT]

class Server(LDAPObject, ResultProcessor):
    """ LDAP connection object with asynchronous searching """
    _server_uri:str

    def __init__(self, uri:str) -> None:
        self._server_uri = uri
        super().__init__(uri)

    async def search(self, base:str, scope:Scope, search:str = "(objectClass=*)", *,
                     attrs:T.Optional[T.List[str]] = None,
                     adaptor:T.Optional[_AdaptorT] = None) -> T.AsyncIterator[_AdaptedT]:
        """
        Invoke an LDAP search and return results asynchronously

        @param   base     Search base DN
        @param   scope    Search scope
        @param   search   Search term
        @kwarg   attrs    List of attributes; None for everything (default)
        @kwarg   adaptor  Function applied to each result; None for no adaption (default)
        @return  Asynchronous generator of (optionally adapted) search results
        """
        adaptor = adaptor or (lambda x: x)

        try:
            msgid = super().search(base, scope.value, search, attrs)

            async for result in _SearchResults(self.allresults(msgid)):
                yield adaptor(result)

        except ldap.NO_SUCH_OBJECT:
            raise NoSuchDistinguishedName(f"Base DN {base} does not exist")

        except ldap.SERVER_DOWN:
            raise CannotConnect(f"Cannot connect to {self._server_uri}")
