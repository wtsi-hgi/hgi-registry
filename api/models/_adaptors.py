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

from api import ldap
from common import types as T
from common.utils import noop


_AttrAdaptorT = T.Callable

class Attribute(object):
    """ Attribute(s) adaptor interface for data munging """
    _attrs:T.Tuple[str, ...]
    _adaptor:_AttrAdaptorT

    def __init__(self, *attrs:str, adaptor:T.Optional[_AttrAdaptorT] = None) -> None:
        assert attrs # Need at least one

        self._attrs = attrs
        self._adaptor = adaptor or noop

    def __call__(self, entity:ldap.Entity) -> T.Any:
        return self._adaptor(*map(entity.get, self._attrs))

# Basic adaptors to flatten/convert simple text attributes
flatten = lambda x: x[0].decode()
to_bool = lambda x: flatten(x).upper() in ["TRUE", "YES"]
