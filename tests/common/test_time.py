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
import json
from datetime import datetime

from common import time


class TestJSONEncoder(unittest.TestCase):
    def test_encoding(self):
        now = time.now().replace(microsecond=0)
        encoded = json.dumps(now, cls=time.JSONEncoder)
        self.assertEqual(now, datetime.strptime(encoded, f"\"{time.ISO8601}\""))

    def test_fallback(self):
        class _Dummy(object):
            pass

        self.assertRaises(TypeError, json.dumps, _Dummy(), cls=time.JSONEncoder)


if __name__ == "__main__":
    unittest.main()
