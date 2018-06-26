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
import api.ldap._entity as e
import api.ldap._server as s
import api.ldap._exceptions as x


def _mock_results(x):
    """
    This generator yields the same structure as that returned by
    ldap.resiter's results generator. It's not clear from the
    documentation why the data tuple is wrapped up in a list, but it's
    not our place to ask...
    """
    for _ in range(x):
        yield "foo", [("dn", {"attribute": "value"})], "bar", "quux"


class TestResultGenerator(unittest.TestCase):
    @async_test
    async def test_generator(self):
        results = 0
        async for dn, entry in s._SearchResults(_mock_results(10)):
            self.assertEqual(dn, "dn")
            self.assertEqual(entry, {"attribute": "value"})
            results += 1

        self.assertEqual(results, 10)


class TestEntity(unittest.TestCase):
    def test_mapping(self):
        entity = e.Entity("foo")
        entity._payload = test_payload = {"foo": 123, "bar": 456}

        self.assertEqual(entity.dn, "foo")
        self.assertEqual(len(entity), len(test_payload))

        for k in entity.keys():
            self.assertEqual(entity[k], test_payload[k])

    def test_not_fetched(self):
        entity = e.Entity("foo")
        self.assertRaises(x.PayloadNotFetched, entity.get, "foo")
        self.assertRaises(x.PayloadNotFetched, iter, entity)
        self.assertRaises(x.PayloadNotFetched, len, entity)

    @async_test
    @patch("api.ldap._server.Server", spec = True)
    async def test_fetch(self, mock_server):
        entity = e.Entity("foo")
        entity.server = mock_server

        mock_server.search.return_value = s._SearchResults(_mock_results(1))
        await entity.fetch()
        self.assertEqual(entity["attribute"], "value")

        mock_server.search.return_value = s._SearchResults(_mock_results(0))
        with self.assertRaises(x.NoSuchDistinguishedName):
            await entity.fetch()
