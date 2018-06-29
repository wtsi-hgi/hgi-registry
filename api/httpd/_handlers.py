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

from ._middleware import allow, accept
from ._types import Request, Response


_JSON = "application/json"
_JPEG = "image/jpeg"

_ENCODING = "utf-8"


@allow("GET")
@accept(_JSON)
async def registry(req:Request) -> Response:
    pass


@allow("GET")
@accept(_JSON)
async def people(req:Request) -> Response:
    pass


@allow("GET")
@accept(_JSON)
async def person(req:Request) -> Response:
    pass


@allow("GET")
@accept(_JPEG)
async def photo(req:Request) -> Response:
    pass


@allow("GET")
@accept(_JSON)
async def groups(req:Request) -> Response:
    pass


@allow("GET")
@accept(_JSON)
async def group(req:Request) -> Response:
    pass
