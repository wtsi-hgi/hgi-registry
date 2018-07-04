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

from http.server import BaseHTTPRequestHandler

from common import types as T, json
from common.constants import ENCODING, MIMEType
from common.logging import Level, log
from ._types import HTTPException


__all__ = ["HTTPError"]


# Extract HTTP client/server error response reasons from stdlib
_status_map:T.Dict[int, str] = {
    status.value: description
    for status, (description, _long_desc) in BaseHTTPRequestHandler.responses.items()
    if 400 <= status.value < 600
}

class HTTPError(HTTPException):
    """ Standardised JSON error response """
    _description:str

    def __init__(self, status_or_exception:T.Union[int, HTTPException], description:T.Optional[str] = None, headers:T.Optional[T.Dict[str, str]] = None) -> None:
        # If an exception is passed, unpack it and rerun
        if isinstance(status_or_exception, HTTPException):
            e = status_or_exception
            self.__init__(e.status_code, description or e.text, headers)
            return

        assert description is not None
        self._description = description

        self.status_code = status_or_exception

        try:
            reason = _status_map[self.status_code]
        except KeyError:
            log(f"HTTP {self.status_code} status is undefined", Level.Debug)
            reason = "Undefined Error"

        headers_with_content_type = {
            "Content-Type": f"{MIMEType.JSON.value}; charset={ENCODING}",
            **(headers or {})
        }

        body = json.encode({
            "status":      self.status_code,
            "reason":      reason,
            "description": self.description
        })

        super().__init__(headers=headers_with_content_type, reason=reason, body=body)

    @property
    def description(self) -> str:
        return self._description
