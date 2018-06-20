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

from . import types as T

noop = lambda *_, **__: None
identity = lambda x: x


_S = T.TypeVar("_S")
_T = T.TypeVar("_T")

def maybe(fn:T.Callable[[_S], _T]) -> T.Callable[[_S], T.Optional[_T]]:
    """ Return a version of a function that returns None if its input is falsy """
    return lambda x: fn(x) if x else None
