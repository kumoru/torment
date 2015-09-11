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

import logging
import os
import typing  # noqa (use mypy typing)
import unittest

from torment import contexts
from torment import fixtures
from torment import helpers

from torment import decorators

logger = logging.getLogger(__name__)


class LogDecoratorFixture(fixtures.Fixture):
    def initialize(self):
        if not hasattr(self, 'parameters'):
            self.parameters = {}

    @property
    def description(self) -> str:
        _description = super().description + '.log'

        if self.parameters.get('prefix') is not None:
            _description += '({0.parameters[prefix]})'

        _description += '({0.function.__name__})'

        return _description.format(self, self.context.module)

    def run(self) -> None:
        if not hasattr(self.context, 'assertLogs'):
            raise unittest.SkipTest('assertLogs not available—added in python-3.4')

        with self.context.assertLogs(decorators.logger, level = logging.DEBUG) as mocked_logger:
            try:
                if hasattr(self.function, '__wrapped__'):
                    self.function()
                else:
                    decorators.log(self.parameters.get('prefix', ''))(self.function)()
            except RuntimeError:
                pass

        self.mocked_logger = mocked_logger

        logger.debug('self.mocked_logger.output: %s', self.mocked_logger.output)

    def check(self) -> None:
        for output in filter(lambda _: 'INFO' in _ or 'EXCEPTION' in _, self.mocked_logger.output):
            self.context.assertTrue(output.startswith(self.expected.pop(0)))


helpers.import_directory(__name__, os.path.dirname(__file__))


class DecoratorUnitTest(contexts.TestContext, metaclass = contexts.MetaContext):
    fixture_classes = (
        LogDecoratorFixture,
    )


class MockDecoratorTest(unittest.TestCase):
    def setUp(self) -> None:
        class context(object):
            mocks_mask = set()

        self.c = context()

    def test_masked_call(self) -> None:
        '''torment.decorators.mock(foo): foo in mocks_mask'''

        self.c.mocks_mask.add('foo')

        self.assertFalse(decorators.mock('foo')(lambda self: None)(self.c))

        self.assertFalse(self.c.is_mocked_foo)

    def test_single_call(self) -> None:
        '''torment.decorators.mock(foo): not called'''

        self.assertTrue(decorators.mock('foo')(lambda self: None)(self.c))

        self.assertTrue(self.c.is_mocked_foo)

    def test_many_call(self) -> None:
        '''torment.decorators.mock(foo): previously called'''

        decorators.mock('foo')(lambda self: None)(self.c)

        self.assertTrue(decorators.mock('foo')(lambda self: None)(self.c))

        logger.debug('dir(self.c): %s', dir(self.c))

        self.assertTrue(self.c.is_mocked_foo)
