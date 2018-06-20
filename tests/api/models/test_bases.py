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

from api.ldap import NoSuchDistinguishedName
from api.models import _adaptors as a
from api.models import _bases as b


class TestNode(unittest.TestCase):
    def test_dn_utils(self):
        base_dn = "ou=foo,dc=example,dc=com"
        rdn_attr = "cn"
        rdn = "testy_mctestface"

        class _TestNode(b.BaseNode):
            _rdn_attr = rdn_attr
            _base_dn = base_dn

        dn = _TestNode.build_dn(rdn)
        self.assertEqual(dn, f"{rdn_attr}={rdn},{base_dn}")

        self.assertEqual(_TestNode.extract_rdn(dn), rdn)
        self.assertRaises(NoSuchDistinguishedName, _TestNode.extract_rdn, "foo")

    def test_getattr(self):
        class _TestNode(b.BaseNode):
            def __init__(self, attr_map):
                self._attr_map = attr_map
                self._entity = {"bar": 123}

            def __serialisable__(self):
                pass

        def _passthrough(*args):
            return args

        node = _TestNode({"foo": a.Attribute("bar", adaptor=_passthrough)})
        self.assertEqual(node.foo, (123,))
        self.assertRaises(AttributeError, getattr, node, "bar")


if __name__ == "__main__":
    unittest.main()
