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

import typing  # flake8: noqa (use mypy typing)

from torment import contexts
from torment import fixtures

from torment import decorators


class LogDecoratorFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        _description = super().description + '.log({0.function.__name__})'

        if self.parameters.get('prefix') is not None:
            _description = _description[:20] + '({0.parameters[prefix]})' + _description[20:]

        return _description.format(self, self.context.module)

    def run(self) -> None:
        pass  # TODO capture logs

    def check(self) -> None:
        pass  # TODO capture logs


class MockDecoratorFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        return super().description + '.mock({0.mock.name})'

    def run(self) -> None:
        pass  # TODO mock symbol

    def check(self) -> None:
        pass  # TODO mock symbol


class DecoratorUnitTest(contexts.TestContext, metaclass = contexts.MetaContext):
    fixture_classes = (
        LogDecoratorFixture,
        MockDecoratorFixture,
    )
