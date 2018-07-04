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

import json

from .constants import ENCODING
from . import time, types as T


__all__ = ["encode"]


class _JSONEncoder(json.JSONEncoder):
    """ JSON encoder that understands all our types """
    _encoders:T.ClassVar[T.List[json.JSONEncoder]] = [
        time.JSONEncoder()
    ]

    def default(self, obj:T.Any) -> T.Any:
        for encoder in _JSONEncoder._encoders:
            try:
                return encoder.default(obj)

            except TypeError:
                pass

        super().default(obj)

def encode(data:T.Any) -> bytes:
    """ Standard JSON encoding """
    return json.dumps(data, cls=_JSONEncoder).encode(ENCODING)
