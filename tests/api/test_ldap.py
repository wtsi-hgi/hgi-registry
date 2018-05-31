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

from tests import async_test
import api.ldap._server as server


class TestResultGenerator(unittest.TestCase):
    def setUp(self):
        def mock_results():
            for _ in range(10):
                yield "foo", [("dn", "entry")], "bar", "quux"

        self.mock_results = mock_results()

    @async_test
    async def test_generator(self):
        async for dn, entry in server._SearchResults(self.mock_results):
            self.assertEqual(dn, "dn")
            self.assertEqual(entry, "entry")
