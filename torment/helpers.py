# Copyright 2015 Alex Brandt <alex.brandt@rackspace.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import importlib
import itertools
import logging
import os
import typing  # noqa (use mypy typing)

from typing import Any
from typing import Dict
from typing import Iterable

from torment import decorators

logger = logging.getLogger(__name__)


def extend(base: Dict[Any, Any], extension: Dict[Any, Any]) -> Dict[Any, Any]:
    '''Extend base by updating with the extension.

    Arguments
    ---------

    :``base``: dictionary to have keys updated or added
    :``extension``: dictionary to update base with

    Return Value(s)
    ---------------

    Resulting dictionary from updating base with extension.

    '''

    _ = copy.deepcopy(base)
    _.update(extension)

    return _


@decorators.log
def import_directory(module_basename: str, directory: str, sort_key = None) -> None:
    '''Load all python modules in directory and directory's children.

    Parameters
    ----------

    :``module_basename``: module name prefix for loaded modules
    :``directory``:       directory to load python modules from
    :``sort_key``:        function to sort module names with before loading

    '''

    logger.info('loading submodules of %s', module_basename)
    logger.info('loading modules from %s', directory)

    filenames = itertools.chain(*[ [ os.path.join(_[0], filename) for filename in _[2] ] for _ in os.walk(directory) if len(_[2]) ])
    modulenames = _filenames_to_modulenames(filenames, module_basename, directory)

    for modulename in sorted(modulenames, key = sort_key):
        try:
            importlib.import_module(modulename)
        except ImportError:
            logger.warning('failed loading %s', modulename)
            logger.exception('module loading failure')
        else:
            logger.info('successfully loaded %s', modulename)


def powerset(iterable: Iterable[Any]) -> Iterable[Iterable[Any]]:
    '''Powerset of iterable.

    **Parameters**

    :``iterable``: set to generate powerset

    **Return Value(s)**

    Generator that produces all subsets of iterable.

    '''

    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s) + 1))


@decorators.log
def _filenames_to_modulenames(filenames: Iterable[str], modulename_prefix: str, filename_prefix: str = '') -> Iterable[str]:
    '''Convert given filenames to module names.

    Any filename that does not have a corresponding module name will be dropped
    from the result (i.e. __init__.py).

    Parameters
    ----------

    :``filename_prefix``:   a prefix to drop from all filenames (typically a
                            common directory); defaults to ''
    :``filenames``:         the filenames to transform into module names
    :``modulename_prefix``: a prefix to add to all module names

    Return Value(s)
    ---------------

    A list of modulenames corresponding to all filenames (for legal module names).

    '''

    modulenames = []  # type: Iterable[str]

    for filename in filenames:
        if not filename.endswith('.py'):
            continue

        name = filename

        name = name.replace(filename_prefix, '')
        name = name.replace('__init__.py', '')
        name = name.replace('.py', '')
        name = name.replace('/', '.')

        name = name.strip('.')

        if not len(name):
            continue

        if not modulename_prefix.endswith('.'):
            modulename_prefix += '.'

        name = modulename_prefix + name

        known_symbols = set()
        name = '.'.join([ _ for _ in name.split('.') if _ not in known_symbols and not known_symbols.add(_) ])

        if len(name):
            modulenames.append(name)

    return modulenames
