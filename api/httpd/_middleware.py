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

from common.logging import Level, log
from ._error import BaseHTTPError, error
from ._types import Application, Request, Response, Handler


async def catch500(_app:Application, handler:Handler) -> Handler:
    """ Internal Server Error catch-all """
    async def _middleware(request:Request) -> Response:
        try:
            return await handler(request)

        except BaseHTTPError as e:
            # Reraise and log known errors
            log(e.description, Level.Error)
            raise

        except Exception as e:
            # Catch and log everything else as a 500 Internal Server Error
            message = str(e)
            log(message, Level.Error)
            raise error(500, message)

    return _middleware
