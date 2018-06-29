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

from aiohttp.web import run_app

from common.logging import Level, get_logger, log
from api.models import Registry
from . import _handlers as handler
from ._middleware import catch500
from ._types import Application, Request, Response


__all__ = ["start"]


async def _shutdown(app:Application) -> None:
    """ Log when the API server is shutdown """
    log("Shutting down API server", Level.Info)


def start(host:str, port:int, registry:Registry) -> None:
    """ Start the API server """
    logger = get_logger()

    app = Application(logger=logger, middlewares=[catch500])
    app.on_shutdown.append(_shutdown)

    app["registry"] = registry

    # Routing
    app.router.add_route("*", "/",                  handler.registry)
    app.router.add_route("*", "/people",            handler.people)
    app.router.add_route("*", "/people/{id}",       handler.person)
    app.router.add_route("*", "/people/{id}/photo", handler.photo)
    app.router.add_route("*", "/groups",            handler.groups)
    app.router.add_route("*", "/groups/{id}",       handler.group)

    log(f"Starting API server on http://{host}:{port}", Level.Info)
    run_app(app, host=host, port=port,
            access_log=logger, access_log_format="%a \"%r\" %s %b",
            print=None)
