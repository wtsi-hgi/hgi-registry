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

from api.models import _adaptors as a
from common import types as T
from common.utils import noop


class TestAttribute(unittest.TestCase):
    def test_zero_mapping(self):
        self.assertRaises(AssertionError, a.Attribute)
        self.assertRaises(AssertionError, a.Attribute, adaptor=noop)

    def test_adaptor(self):
        def _entity_values(*args) -> T.Tuple:
            return args

        # Should be api.ldap.Entity, but any Mappable will work
        entity = {"foo": 1, "bar": 2, "quux": 3}

        adapt = a.Attribute("foo", adaptor=_entity_values)
        self.assertEqual(adapt(entity), (1,))

        adapt = a.Attribute("bar", adaptor=_entity_values)
        self.assertEqual(adapt(entity), (2,))

        adapt = a.Attribute("quux", adaptor=_entity_values)
        self.assertEqual(adapt(entity), (3,))

        adapt = a.Attribute("foo", "bar", adaptor=_entity_values)
        self.assertEqual(adapt(entity), (1, 2))

        adapt = a.Attribute("foo", "quux", adaptor=_entity_values)
        self.assertEqual(adapt(entity), (1, 3))

        adapt = a.Attribute("bar", "quux", adaptor=_entity_values)
        self.assertEqual(adapt(entity), (2, 3))

        adapt = a.Attribute("quux", "bar", "foo", adaptor=_entity_values)
        self.assertEqual(adapt(entity), (3, 2, 1))


if __name__ == "__main__":
    unittest.main()
