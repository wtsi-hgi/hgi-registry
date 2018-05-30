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

from ldap.ldapobject import LDAPObject
from ldap.resiter import ResultProcessor

from common import types as T
from ._scope import Scope


_EntryT = T.Dict[str, T.List[T.Union[T.Text, T.ByteString]]]

class _SearchResults(T.AsyncIterator[T.Tuple[str, _EntryT]]):
    """ Asynchronous generator from LDAP search generator """
    def __init__(self, results) -> None:
        self._results = results

    def __aiter__(self):
        return self

    async def __anext__(self) -> T.Tuple[str, _EntryT]:
        """ Iterate through generator """
        try:
            _, [(dn, entry)], _, _ = next(self._results)

        except StopIteration:
            raise StopAsyncIteration

        return dn, entry


class LDAPServer(LDAPObject, ResultProcessor):
    """ LDAP connection object with asynchronous searching """
    async def search(self, base:str, scope:Scope, search:str = "(objectClass=*)", attrs:T.Optional[T.List[str]] = None) -> _SearchResults:
        """
        Invoke an LDAP search and return results asynchronously

        @param   base    Search base DN
        @param   scope   Search scope
        @param   search  Search term
        @param   attrs   List of attributes; None for everything (default)
        @return  Asynchronous generator of DN/entry tuples
        """
        msgid = super().search(base, scope.value, search, attrs)
        async for result in _SearchResults(self.allresults(msgid)):
            yield result
