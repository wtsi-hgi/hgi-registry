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


_EntryT = T.Dict[str, T.Union[T.Text, T.ByteString]]

class LDAPServer(LDAPObject, ResultProcessor):
    """ LDAP connection object with asynchronous searching """
    async def search(self, base:str, scope:Scope, search:str = "(objectClass=*)", attrs:T.Optional[T.List[str]] = None) -> T.AsyncIterator[T.Tuple[str, _EntryT]]:
        """
        Invoke an LDAP search and return results asynchronously

        @param   base    Search base DN
        @param   scope   Search scope
        @param   search  Search term
        @param   attrs   List of attributes; None for everything (default)
        @return  Asynchronous generator of DN/entry tuples
        """
        msgid = super().search(base, scope.value, search, attrs)

        async for _type, data, _msgid, _controls in self.allresults(msgid):
            # data is a tuple of DN (string) and payload (dictionary)
            yield data
