"""
Copyright (c) 2017 Genome Research Ltd.

Author: Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import asyncio
import typing as T
from functools import wraps


def async_test(fn_or_loop:T.Union[T.Callable, asyncio.BaseEventLoop, None] = None) -> T.Callable:
    """
    Decorator for testing asynchronous code

    @param   fn_or_loop  Function to decorate (i.e., decorator used with no invocation)
                         OR event loop to use (i.e., parametrised decorator)
    """
    parametrised = isinstance(fn_or_loop, (asyncio.BaseEventLoop, type(None)))
    loop = fn_or_loop if parametrised else asyncio.get_event_loop()

    def _decorator(fn:T.Callable) -> T.Callable:
        @wraps(fn)
        def _decorated(*args, **kwargs):
            coroutine = asyncio.coroutine(fn)
            future = coroutine(*args, **kwargs)
            loop.run_until_complete(future)

        return _decorated

    return _decorator if parametrised else _decorator(fn_or_loop)
