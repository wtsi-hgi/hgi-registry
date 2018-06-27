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

from aiohttp.web import HTTPError

from common import types as T
from common.logging import Level, log


__all__ = ["BaseHTTPError", "error"]


_ENCODING = "utf-8"

_status_map:T.Dict[int, str] = {
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    500: "Internal Server Error",
    502: "Bad Gateway"
}

class BaseHTTPError(HTTPError):
    """ Standardised JSON error response """
    description:str

    def __init__(self, description:str, headers:T.Optional[T.Dict[str, str]] = None) -> None:
        try:
            reason = _status_map[self.status_code]

        except KeyError:
            log(f"HTTP {self.status_code} status is undefined", Level.Debug)
            reason = "Undefined Error"

        self.description = description

        headers_with_content_type = {
            "Content-Type": f"application/json; charset={_ENCODING}",
            **(headers or {})
        }

        body = json.dumps({
            "status":      self.status_code,
            "reason":      reason,
            "description": description
        }).encode(_ENCODING)

        super().__init__(headers=headers_with_content_type, reason=reason, body=body)


def error(status:int, description:str, *, headers:T.Optional[T.Dict[str, str]] = None) -> BaseHTTPError:
    """ Error factory """
    class _HTTPError(BaseHTTPError):
        status_code = status

    return _HTTPError(description, headers)
