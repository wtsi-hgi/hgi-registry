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

import asyncio
import json
from functools import wraps

from api.ldap import CannotConnect, Server
from api.models import Registry, Person, Group
from common import types as T, time
from common.logging import Level, log
from ._error import HTTPError
from ._middleware import allow, accept
from ._types import Request, Response, Handler, HandlerDecorator


_JSON = "application/json"
_JPEG = "image/jpeg"

_ENCODING = "utf-8"

_MAX_RETRY = 3


def _reconnect(max_attempts:int = 1) -> HandlerDecorator:
    """
    Parametrisable handler decorator that will reattempt to run the
    handler a set number of times while, in the event of a connection
    problem with the LDAP server, trying to reconnect
    """
    assert max_attempts > 0

    def _decorator(handler:Handler) -> Handler:
        @wraps(handler)
        async def _decorated(req:Request) -> Response:
            registry = req.app["registry"]
            ldap_server = registry.server.uri

            attempt = max_attempts
            sleep_for = 1
            while attempt:
                try:
                    return await handler(req)

                except CannotConnect:
                    attempt -= 1
                    if not attempt:
                        # Bad gateway
                        raise HTTPError(502, f"Cannot establish a connection with LDAP server at {ldap_server}")

                    # Otherwise, sleep for a bit, then try reconnecting
                    log(f"Will attempt to reconnect to LDAP server at {ldap_server} in {sleep_for} seconds...", Level.Debug)
                    await asyncio.sleep(sleep_for)
                    ldap = Server(ldap_server)
                    registry.server = ldap

                    # Exponential back-off
                    sleep_for *= 2

        return _decorated

    return _decorator


async def _get_registry(req:Request) -> Registry:
    """ Get (and update, if necessary) the Registry object """
    registry = req.app["registry"]
    if registry.has_expired:
        await registry.update()

    return registry


def _JSONResponse(body:T.Any, *, serialise:bool = True, status:int = 200) -> Response:
    """ Standardised Response factory for JSON payloads """
    return Response(status=status, content_type=_JSON, charset=_ENCODING,
                    body=json.dumps(body, cls=time.JSONEncoder).encode(_ENCODING) if serialise else body)


@allow("GET")
@accept(_JSON)
@_reconnect(_MAX_RETRY)
async def registry(req:Request) -> Response:
    # Index (undocumented endpoint, just for completeness)
    registry = await _get_registry(req)
    return _JSONResponse({
        "last_updated": registry.last_updated,
        "groups":       { "href": "/groups", "rel": "items" },
        "people":       { "href": "/people", "rel": "items" }
    })


@allow("GET")
@accept(_JSON)
@_reconnect(_MAX_RETRY)
async def people(req:Request) -> Response:
    registry = await _get_registry(req)
    return _JSONResponse(await registry.all(Person))


@allow("GET")
@accept(_JSON)
@_reconnect(_MAX_RETRY)
async def person(req:Request) -> Response:
    identity = req.match_info['id']
    raise NotImplementedError(f"Not yet implemented; ID {identity}")


@allow("GET")
@accept(_JPEG)
@_reconnect(_MAX_RETRY)
async def photo(req:Request) -> Response:
    identity = req.match_info['id']
    raise NotImplementedError(f"Not yet implemented; ID {identity}")


@allow("GET")
@accept(_JSON)
@_reconnect(_MAX_RETRY)
async def groups(req:Request) -> Response:
    registry = await _get_registry(req)
    return _JSONResponse(await registry.all(Group))


@allow("GET")
@accept(_JSON)
@_reconnect(_MAX_RETRY)
async def group(req:Request) -> Response:
    identity = req.match_info['id']
    raise NotImplementedError(f"Not yet implemented; ID {identity}")
