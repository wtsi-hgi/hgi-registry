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

import unittest
from unittest.mock import patch

from tests import async_test
from api.models import _mixins as m
from common import types as T, time


class DummyExpirable(m.Expirable):
    update_count:int

    async def __updator__(self) -> None:
        if not hasattr(self, "update_count"):
            self.update_count = 0

        self.update_count = self.update_count + 1

class TestExpirable(unittest.TestCase):
    @async_test
    async def test_update(self):
        expirable = DummyExpirable(time.delta(1))
        self.assertIsNone(expirable.last_updated)

        with patch("api.models._mixins.time", spec=True) as mock_time:
            mock_time.now.return_value = 123
            await expirable.update()

        self.assertEqual(expirable.last_updated, 123)
        self.assertEqual(expirable.update_count, 1)

        await expirable.update()
        self.assertEqual(expirable.update_count, 2)

    def test_expiry(self):
        expirable = DummyExpirable(123)
        self.assertTrue(expirable.has_expired)

        with patch("api.models._mixins.time", spec=True) as mock_time:
            expirable._last_updated = 0

            mock_time.now.return_value = 1
            self.assertFalse(expirable.has_expired)

            mock_time.now.return_value = 123
            self.assertFalse(expirable.has_expired)

            mock_time.now.return_value = 124
            self.assertTrue(expirable.has_expired)


class DummySerialisable(m.Serialisable):
    async def __serialisable__(self) -> T.Any:
        return "foo"

class TestSerialisable(unittest.TestCase):
    @async_test
    async def test_json_serialisation(self):
        serialisable = DummySerialisable()
        json = await serialisable.json
        self.assertEqual(json, "\"foo\"")


class DummyHypermedia(m.Hypermedia):
    _base_uri = "/base"

    @property
    def identity(self) -> str:
        return "foo"

class TestHypermedia(unittest.TestCase):
    def test_href(self):
        hyper = DummyHypermedia()

        self.assertRaises(AssertionError, DummyHypermedia.href, hyper)

        self.assertEqual(DummyHypermedia.href(hyper, rel="foo"), {
            "href": "/base/foo",
            "rel": "foo"
        })

        self.assertEqual(DummyHypermedia.href(hyper, rev="foo"), {
            "href": "/base/foo",
            "rev": "foo"
        })

        self.assertEqual(DummyHypermedia.href(hyper, rel="foo", rev="bar"), {
            "href": "/base/foo",
            "rel": "foo",
            "rev": "bar"
        })

        self.assertEqual(DummyHypermedia.href(hyper, rel="foo", value="bar"), {
            "href": "/base/foo",
            "rel": "foo",
            "value": "bar"
        })


if __name__ == "__main__":
    unittest.main()
