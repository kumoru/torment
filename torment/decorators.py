# Copyright 2015 Alex Brandt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import inspect
import logging
import typing  # noqa (use mypy typing)

from typing import Any
from typing import Callable

logger = logging.getLogger(__name__)
logger.propogate = False
logger.addHandler(logging.NullHandler())


def log(prefix = ''):
    '''Add start and stop logging messages to the function.

    Parameters
    ----------

    :``prefix``: a prefix for the function name (optional)

    '''

    function = None

    if inspect.isfunction(prefix):
        prefix, function = '', prefix

    def _(function):
        @functools.wraps(function, assigned = functools.WRAPPER_ASSIGNMENTS + ( '__file__', ))
        def wrapper(*args, **kwargs):
            name, my_args = function.__name__, args

            if inspect.ismethod(function):
                name = function.__self__.__class__.__name__ + '.' + function.__name__
            elif len(args):
                members = dict(inspect.getmembers(args[0], predicate = lambda _: inspect.ismethod(_) and _.__name__ == function.__name__))
                logger.debug('members: %s', members)

                if len(members):
                    name, my_args = args[0].__class__.__name__ + '.' + function.__name__, args[1:]

            format_args = (
                prefix + name,
                ', '.join(list(map(str, my_args)) + [ ' = '.join(map(str, item)) for item in kwargs.items() ]),
            )

            logger.info('STARTING: %s(%s)', *format_args)

            try:
                return function(*args, **kwargs)
            except:
                logger.exception('EXCEPTION: %s(%s)', *format_args)
                raise
            finally:
                logger.info('STOPPING: %s(%s)', *format_args)

        return wrapper

    if function is not None:
        _ = _(function)

    return _


def mock(name: str) -> Callable[[Any], None]:
    '''Setup properties indicating status of name mock.

    This is designed to decorate ``torment.TestContext`` methods and is used to
    provide a consistent interface for determining if name is mocked once and
    only once.

    Parameters
    ----------

    :``name``: symbol in context's module to mock

    Return Value(s)
    ---------------

    True if name is mocked; otherwise, False.  Also, creates a property on the
    method's self, is_mocked_name, with this value.

    '''

    def _(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            logger.info('STARTING: mock ' + name)

            is_mocked = False

            sanitized_name = name.replace('.', '_').strip('_')

            if name in self.mocks_mask:
                logger.info('STOPPING: mock ' + name + '—MASKED')
            elif getattr(self, 'is_mocked_' + sanitized_name, False):
                is_mocked = True

                logger.info('STOPPING: mock ' + name + '—EXISTS')
            else:
                func(self, *args, **kwargs)

                is_mocked = True

                logger.info('STOPPING: mock ' + name)

            setattr(self, 'is_mocked_' + sanitized_name, is_mocked)

            return is_mocked

        return wrapper

    return _
