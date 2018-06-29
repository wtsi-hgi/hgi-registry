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

from common import time
from common.logging import Level, log
from . import httpd
from .ldap import Server
from .models import Registry


if __name__ == "__main__":
    log("Human Genetics Programme Registry API Server", Level.Info)

    if "LDAP_URI" not in os.environ:
        log("LDAP_URI environment variable is not defined", Level.Critical)
        sys.exit(1)

    ldap = Server(os.environ["LDAP_URI"])

    expiry = int(os.environ.get("EXPIRY", 3600))
    registry = Registry(ldap, time.delta(seconds=expiry))

    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("API_PORT", 5000))
    httpd.start(host, port, registry)
