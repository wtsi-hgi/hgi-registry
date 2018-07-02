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

import os
import sys
from urllib.parse import urlparse

from common import time
from common.logging import Level, log
from . import httpd, __version__
from .ldap import Server
from .models import Registry


if __name__ == "__main__":
    log(f"Human Genetics Programme Registry API Server {__version__}", Level.Info)

    if "LDAP_URI" not in os.environ:
        log("LDAP_URI environment variable is not defined", Level.Critical)
        sys.exit(1)

    ldap = Server(os.environ["LDAP_URI"])

    expiry = time.delta(seconds=int(os.environ.get("EXPIRY", 3600)))
    registry = Registry(ldap, expiry)

    api_uri = urlparse(os.environ.get("API_URI", "http://127.0.0.1:5000"))
    if not (api_uri.scheme == "http" and api_uri.hostname and api_uri.port):
        log("Invalid value for API_URI environment variable", Level.Critical)
        sys.exit(1)

    httpd.start(api_uri.hostname, api_uri.port, registry)
