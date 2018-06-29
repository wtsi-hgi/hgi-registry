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

import re
from functools import wraps, total_ordering

from common import types as T
from common.logging import Level, log
from ._error import BaseHTTPError, error
from ._types import Application, Request, Response, Handler


__all__ = ["catch500", "allow", "accept"]

_HandlerDecoratorT = T.Callable[[Handler], Handler]


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


def allow(*methods:str) -> _HandlerDecoratorT:
    """
    Parametrisable handler decorator which checks the request method
    matches what's allowed (raising an error, if not) and responds
    appropriately to an OPTIONS request
    """
    # Allowed methods, obviously including OPTIONS and automatically
    # providing HEAD support
    allowed = {m.upper() for m in [*methods, "OPTIONS", "HEAD"]}
    allow_header = {"Allow": ", ".join(allowed)}

    def _decorator(handler:Handler) -> Handler:
        """ Decorator that handles the allowed methods """
        @wraps(handler)
        async def _decorated(request:Request) -> Response:
            """ Check request method against allowed methods """
            if request.method not in allowed:
                raise error(405, f"Cannot {request.method} the resource at {request.url}.", headers=allow_header)

            if request.method == "OPTIONS":
                return Response(status=200, headers=allow_header)

            response = await handler(request)

            if request.method == "HEAD":
                content_length = len(response.body)
                response.body = None
                response.headers["Content-Length"] = str(content_length)

            return response

        return _decorated

    return _decorator


# Media type naming per RFC6838
# https://tools.ietf.org/html/rfc6838#section-4.2
RE_MEDIA_TYPE = re.compile(r"""
    # Type and subtype between 1 and 64 characters
    (?= ^ [^/]{1,64} / [^/]{1,64} $ )

    (?:^
        (?P<type>
            [a-z0-9]
            [a-z0-9!#\$&\-^_\.\+]{,126}
        )
        /
        (?P<subtype>
            [a-z0-9]
            [a-z0-9!#\$&\-^_\.\+]{,126}
        )
    $)
""", re.VERBOSE | re.IGNORECASE)

_RE_COMMA_SEP = re.compile(r"\s*,\s*")
_RE_SEMICOLON_SEP = re.compile(r"\s*;\s*")
_RE_EQUAL_SEP = re.compile(r"\s*=\s*")

@total_ordering
class _MediaRange(object):
    """ Parametrised media range """
    media_range:str
    q:float
    params:T.Dict[str, T.Any]

    def __init__(self, media_range:str, **params) -> None:
        self.media_range = media_range
        self.q = float(params.get("q", 1.0))
        self.params = {k: v for k, v in params.items() if not k == "q"}

    def in_range(self, media_type:str, **params) -> bool:
        """ Check the supplied media type is in the media range """
        range_type, range_subtype = self.media_range.split("/")
        if range_type == range_subtype == "*":
            # Accept all
            return True

        _m = RE_MEDIA_TYPE.match(media_type)
        mt_type = _m["type"]
        mt_subtype = _m["subtype"]

        if mt_type == range_type and range_subtype == "*":
            # Accept any subtype
            return True

        return mt_type == range_type \
               and mt_subtype == range_subtype \
               and {k: v for k, v in params.items() if not k == "q"} == self.params

    def __eq__(self, other:"_MediaRange") -> bool:
        return self.media_range == other.media_range \
               and self.params == other.params

    def __lt__(self, other:"_MediaRange") -> bool:
        # This is not a typo :)
        return self.q > other.q

class _AcceptParser(object):
    """
    Parse the HTTP Accept request header and provide an interface for
    choosing the most appropriate media type
    """
    media_ranges:T.List[_MediaRange]

    def __init__(self, accept_header:str = "*/*") -> None:
        _ranges:T.List[_MediaRange] = []

        for m in _RE_COMMA_SEP.split(accept_header):
            media_range, *_params = _RE_SEMICOLON_SEP.split(m)
            params = dict(_RE_EQUAL_SEP.split(p) for p in _params)
            _ranges.append(_MediaRange(media_range, **params))

        # The "most acceptable" media range is the first element of the
        # list and decreases in priority; `sorted` is stable, so relative
        # ordering (based on the input string) is preserved
        self.media_ranges = sorted(_ranges)

    def can_accept(self, *media_types:str) -> bool:
        """
        Check any of the specified media types fulfil those deemed
        acceptable by the client
        """
        return any(r.in_range(m) for m in media_types for r in self.media_ranges)

    def preferred(self, *media_types:str) -> str:
        """
        Determine the most preferred media type from those specified, as
        deemed by the client. In case of a tie, the order in which the
        client specifies acceptable media types will be used (i.e.,
        leftmost first)

        NOTE  We presume that can_accept is true and already tested, so
              this will always return a valid media type
        """
        for r in self.media_ranges:
            for m in media_types:
                if r.in_range(m):
                    return m

def accept(*media_types:str) -> _HandlerDecoratorT:
    """
    Parametrisable handler decorator which checks the requested 
    acceptable media types can be fulfilled (raising an error, if not)
    """
    # Available media types
    if not media_types or any(not RE_MEDIA_TYPE.match(m) for m in media_types):
        raise TypeError("You must specify fully-qualified media type(s)")

    available = tuple(set(media_types))

    def _decorator(handler:Handler) -> Handler:
        """ Decorator that handles the accepted media types """
        @wraps(handler)
        async def _decorated(request:Request) -> Response:
            """ Check Accept header against acceptable media types """
            # Client accepts anything if no Accept value found
            acceptable = _AcceptParser(request.headers.get("Accept", "*/*"))

            if not acceptable.can_accept(*available):
                _pretty = " or".join(", ".join(available).rsplit(",", 1))
                raise error(406, f"Can only respond with {_pretty} media types")

            # Thread the parsed Accept header and the preferred response
            # media type into the request for downstream handlers
            request.can_accept = acceptable.can_accept
            request.preferred  = acceptable.preferred(*available)
            return await handler(request)

        return _decorated

    return _decorator
