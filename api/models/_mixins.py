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
import json

from common import types as T, time


class Expirable(metaclass=ABCMeta):
    """ Base class for items that ought to be periodically updated """
    _last_updated:T.Optional[T.DateTime]
    _shelf_life:T.TimeDelta

    def __init__(self, shelf_life:T.TimeDelta) -> None:
        self._last_updated = None
        self._shelf_life = shelf_life

    @abstractmethod
    async def __updator__(self) -> None:
        """ Update the object's state """

    @property
    def shelf_life(self) -> T.TimeDelta:
        return self._shelf_life

    @property
    def has_expired(self) -> bool:
        """ Has our entity expired? """
        if self._last_updated is None:
            return True

        age = time.now() - self._last_updated
        return age > self._shelf_life

    @property
    def last_updated(self) -> T.Optional[T.DateTime]:
        return self._last_updated

    async def update(self) -> None:
        self._last_updated = time.now()
        await self.__updator__()

    def expire(self) -> None:
        """ Forcibly expire """
        self._last_updated = None


class Serialisable(metaclass=ABCMeta):
    """ Base class for JSON-serialisable objects """
    @property
    async def json(self) -> str:
        """ Return the JSON serialisation of the object's serialisable form """
        serialisable = await self.__serialisable__()
        return json.dumps(serialisable, cls=time.JSONEncoder)

    @abstractmethod
    async def __serialisable__(self) -> T.Any:
        """ Render a serialisable form of the object """


class Hypermedia(metaclass=ABCMeta):
    """ Base class for hypermedia references """
    _base_uri:T.ClassVar[str]

    @property
    @abstractmethod
    def identity(self) -> str:
        """ Object's identity for its URI """

    @staticmethod
    def href(link:"Hypermedia", *, rel:T.Optional[str] = None, rev:T.Optional[str] = None, value:T.Any = None) -> T.Dict:
        """ Return the hypermedia reference to a hypermedia entity """
        assert rel or rev

        return {
            "href": f"{link._base_uri}/{link.identity}",
            **({"rel": rel} if rel else {}),
            **({"rev": rev} if rev else {}),
            **({"value": value} if value else {})
        }
