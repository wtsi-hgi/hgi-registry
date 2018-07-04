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

from api.models import _humgen as h


class TestPerson(unittest.TestCase):
    def test_decode_photo(self):
        photo = b"abc123"
        self.assertIsNone(h.Person.decode_photo(None))
        self.assertEqual(h.Person.decode_photo([photo]), photo)

    def test_is_human(self):
        self.assertFalse(h.Person.is_human(None))
        self.assertFalse(h.Person.is_human([]))
        self.assertTrue(h.Person.is_human([b"YES"]))
        self.assertTrue(h.Person.is_human([b"NO"]))

    def test_is_active(self):
        self.assertFalse(h.Person.is_active(None, None))
        self.assertFalse(h.Person.is_active([], None))
        self.assertFalse(h.Person.is_active(None, []))
        self.assertFalse(h.Person.is_active([], []))
        self.assertFalse(h.Person.is_active([b"NO"], [b"FALSE"]))
        self.assertTrue(h.Person.is_active([b"YES"], [b"FALSE"]))
        self.assertTrue(h.Person.is_active([b"NO"], [b"TRUE"]))
        self.assertTrue(h.Person.is_active([b"YES"], [b"TRUE"]))


if __name__ == "__main__":
    unittest.main()
