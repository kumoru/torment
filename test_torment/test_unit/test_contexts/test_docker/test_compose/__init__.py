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
import unittest

from torment import contexts
from torment import decorators
from torment import fixtures
from torment import helpers

from torment.contexts.docker import compose

logger = logging.getLogger(__name__)


class CallWrapperFixture(fixtures.Fixture):
    def __init__(self, context) -> None:
        super().__init__(context)

        self.parameters = {}

    @property
    def description(self) -> str:
        return super().description + '.{0.function_name}()'.format(self)

    def setup(self) -> None:
        logger.debug('self.expected: %s', self.expected)

        self.expected = [ unittest.mock.call(*arguments[0], **arguments[1]) for arguments in self.expected ]

        if self.context.mock_call():
            self.context.mocked_call.return_value = 0

    def run(self) -> None:
        getattr(compose, self.function_name)(**self.parameters)

    def check(self) -> None:
        self.context.mocked_call.assert_has_calls(self.expected)


class UpFixture(CallWrapperFixture):
    @property
    def description(self) -> str:
        return super().description[:-1] + '{0.parameters[services]})'.format(self)

helpers.import_directory(__name__, os.path.dirname(__file__))


class CallWrapperUnitTest(contexts.TestContext, metaclass = contexts.MetaContext):
    fixture_classes = (
        CallWrapperFixture,
    )

    mocks = set()  # type: Set[str]

    mocks.add('call')

    @decorators.mock('_call')
    def mock_call(self) -> None:
        self.patch('_call')
