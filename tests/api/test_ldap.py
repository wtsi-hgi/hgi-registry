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
import api.ldap._server as ldap


def _mock_results():
    """
    This generator yields the same structure as that returned by
    ldap.resiter's results generator. It's not clear from the
    documentation why the data tuple is wrapped up in a list, but it's
    not our place to ask...
    """
    for _ in range(10):
        yield "foo", [("dn", "entry")], "bar", "quux"


class TestResultGenerator(unittest.TestCase):
    @async_test
    async def test_generator(self):
        async for dn, entry in ldap._SearchResults(_mock_results()):
            self.assertEqual(dn, "dn")
            self.assertEqual(entry, "entry")
