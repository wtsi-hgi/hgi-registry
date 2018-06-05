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

from common import types as T, time
from . import ldap


class _DataExpired(BaseException):
    """ Raised when an _Expirable has passed its shelf life """

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

_noop    = lambda x: x
_flatten = lambda x: x[0].decode()  # Adaptor to flatten simple text attributes

class _Attribute(object):
    """ Potentially optional attribute, with an adaptor to munge data """
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
    _entity:ldap.Entity
    _attr_map:T.Dict[str, T.Tuple[str, _AttrAdaptorT]]

    def __init__(self, entity:ldap.Entity, attr_map:T.Dict[str, _Attribute], shelf_life:T.TimeDelta) -> None:
        super().__init__(shelf_life)
        self._entity = entity
        self._attr_map = attr_map

    def __getattr__(self, attr:str) -> str:
        if attr not in self._attr_map:
            raise AttributeError(f"No such attribute {attr}!")

        if self.has_expired():
            raise _DataExpired

        return self._attr_map[attr](self._entity)

    async def __updator__(self, *_, **__) -> None:
        await self._entity.fetch()


class Person(_Node):
    def __init__(self, entity:ldap.Entity, shelf_life:T.TimeDelta) -> None:
        attr_map = {
            "name":    _Attribute("cn"),
            "mail":    _Attribute("mail"),
            "title":   _Attribute("title", default="?"),
            "manager": _Attribute("manager", default="?")
        }

        super().__init__(entity, attr_map, shelf_life)


class Group(_Node):
    pass


class _Tree(T.Container["_Node"]):
    pass
