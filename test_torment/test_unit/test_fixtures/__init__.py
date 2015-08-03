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

import copy
import inspect
import logging
import typing  # noqa (use mypy typing)
import unittest
import uuid

from torment import fixtures

logger = logging.getLogger(__name__)


class FixturesCreateUnitTest(unittest.TestCase):
    def test_fixture_create_without_context(self) -> None:
        '''torment.fixtures.Fixture() → TypeError'''

        self.assertRaises(TypeError, fixtures.Fixture)

    def test_fixture_create_with_context(self) -> None:
        '''torment.fixtures.Fixture(context).context == context'''

        c = unittest.TestCase()
        f = fixtures.Fixture(c)

        self.assertEqual(f.context, c)


class FixturesPropertyUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.c = unittest.TestCase()
        self.f = fixtures.Fixture(self.c)

    def test_fixture_category(self) -> None:
        '''torment.fixtures.Fixture(context).category == 'fixtures' '''

        self.f.__module__ = unittest.mock.MagicMock(__name__ = 'test_torment.test_unit.test_fixtures.fixture_a44bc6dda6654b1395a8c2cbd55d964d')

        self.assertEqual(self.f.category, 'fixtures')

    def test_fixture_description(self) -> None:
        '''torment.fixtures.Fixture(context).description == '94d7c58f6ee44683936c21cb84d1e458—torment.fixtures' '''

        self.f.context.module = 'fixtures'
        self.f.uuid = uuid.UUID('94d7c58f6ee44683936c21cb84d1e458')

        self.assertEqual(self.f.description, '94d7c58f6ee44683936c21cb84d1e458—fixtures')

    def test_fixture_name(self) -> None:
        '''torment.fixtures.Fixture(context).name == 'test_94d7c58f6ee44683936c21cb84d1e458' '''

        self.f.__class__.__name__ = '94d7c58f6ee44683936c21cb84d1e458'

        self.assertEqual(self.f.name, 'test_94d7c58f6ee44683936c21cb84d1e458')


class OfUnitTest(unittest.TestCase):
    def test_of_zero(self) -> None:
        '''torment.fixtures.of(()) == []'''

        self.assertEqual(len(fixtures.of(())), 0)

    def test_of_many_without_subclasses(self) -> None:
        '''torment.fixtures.of(( FixtureA, )) == []'''

        class FixtureA(object):
            def __init__(self, context) -> None:
                pass

        self.assertEqual(len(fixtures.of(( FixtureA, ))), 0)

    def test_of_many_with_subclasses(self) -> None:
        '''torment.fixtures.of(( FixtureA, )) == [ fixture_a, ]'''

        class FixtureA(object):
            def __init__(self, context) -> None:
                pass

        class FixtureB(FixtureA):
            pass

        result = fixtures.of(( FixtureA, ))

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], FixtureB)


class RegisterUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        _ = unittest.mock.patch('torment.fixtures.inspect')
        mocked_inspect = _.start()
        self.addCleanup(_.stop)

        mocked_inspect.configure_mock(**{ 'isclass': inspect.isclass, 'isfunction': inspect.isfunction, })

        mocked_inspect.stack.return_value = ( None, ( None, 'test_unit/test_d43830e2e9624dd19c438b15250c5818.py', ), )

        class ContextStub(object):
            pass

        self.context = ContextStub()
        self.context.module = mocked_inspect.getmodule.return_value = 'stack'

        self.ns = {}  # type: Dict[str, Any]
        self.class_name = 'f_d43830e2e9624dd19c438b15250c5818'

    def test_zero_properties(self) -> None:
        '''torment.fixtures.register({}, (), {})'''

        fixtures.register(self.ns, ( fixtures.Fixture, ), {})

        _ = self.ns[self.class_name](self.context)

        self.assertEqual(_.uuid, uuid.UUID('d43830e2e9624dd19c438b15250c5818'))

    def test_one_literal_properties(self) -> None:
        '''torment.fixtures.register({}, (), { 'a': 'a', })'''

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'a': 'a', })

        _ = self.ns[self.class_name](self.context)

        self.assertEqual(_.a, 'a')

    def test_one_class_properties(self) -> None:
        '''torment.fixtures.register({}, (), { 'a': class, })'''

        class A(object):
            pass

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'a': A, })

        _ = self.ns[self.class_name](self.context)

        self.assertIsInstance(_.a, A)

    def test_one_fixture_class_properties(self) -> None:
        '''torment.fixtures.register({}, (), { 'a': fixture_class, })'''

        class A(fixtures.Fixture):
            pass

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'a': A, })

        _ = self.ns[self.class_name](self.context)

        self.assertIsInstance(_.a, A)
        self.assertEqual(_.a.context, self.context)

    def test_one_function_properties(self) -> None:
        '''torment.fixtures.register({}, (), { 'a': self → None, })'''

        def a(self) -> None:
            pass

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'a': a, })

        _ = self.ns[self.class_name](self.context)

        self.assertIsNone(_.a)

    def test_description_property(self) -> None:
        '''torment.fixtures.register({}, (), { 'description': 'needle', })'''

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'description': 'needle', })

        _ = self.ns[self.class_name](self.context)

        self.assertEqual(_.description, 'd43830e2e9624dd19c438b15250c5818—stack—needle')

    def test_error_property(self) -> None:
        '''torment.fixtures.register({}, (), { 'error': …, })'''

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'error': { 'class': RuntimeError, }, })

        _ = self.ns[self.class_name](self.context)

        self.assertIsInstance(_.error, RuntimeError)


class ResolveFunctionsUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        class StubFixture(object):
            pass

        self.f = StubFixture()
        self.f.name = 'testing_fixture_stub'

        self.o = copy.deepcopy(self.f)

    def test_zero_functions(self) -> None:
        '''torment.fixtures._resolve_functions({}, fixture)'''

        fixtures._resolve_functions({}, self.f)

        self.assertEqual(dir(self.o), dir(self.f))

    def test_one_functions_without_parameters(self) -> None:
        '''torment.fixtures._resolve_functions({ 'a': ø → None, }, fixture)'''

        def a() -> None:
            pass

        fixtures._resolve_functions({ 'a': a, }, self.f)

        self.assertEqual(id(self.f.a), id(a))

    def test_one_functions_with_self_parameter(self) -> None:
        '''torment.fixtures._resolve_functions({ 'a': self → None, }, fixture)'''

        def a(self) -> None:
            pass

        fixtures._resolve_functions({ 'a': a, }, self.f)

        self.assertIsNone(self.f.a)

    def test_one_functions_with_self_parameter_raises_attributeerror(self) -> None:
        '''torment.fixtures._resolve_functions({ 'a': self → self.b, }, fixture)'''

        def a(self):
            return self.b

        fixtures._resolve_functions({ 'a': a, }, self.f)

        self.assertEqual(id(self.f.a), id(a))

    def test_many_functions(self) -> None:
        '''torment.fixtures._resolve_functions({ 'a': self → self.b, 'b': self → None, }, fixture)'''

        def a(self) -> None:
            return self.b

        def b(self) -> None:
            pass

        fixtures._resolve_functions({ 'a': a, 'b': b, }, self.f)

        self.assertIsNone(self.f.a)
        self.assertIsNone(self.f.b)


class UniqueClassNameUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.uuid = uuid.uuid4()

    def test_empty_namespace(self) -> None:
        '''torment.fixtures._unique_class_name({}, uuid) == 'f_{uuid}' '''

        n = fixtures._unique_class_name({}, self.uuid)

        self.assertEqual(n, 'f_' + self.uuid.hex)

    def test_one_namespace(self) -> None:
        '''torment.fixtures._unique_class_name({ 'f_{uuid}': None, }, uuid) == 'f_{uuid}_1' '''

        n = fixtures._unique_class_name({ 'f_' + self.uuid.hex: None, }, self.uuid)

        self.assertEqual(n, 'f_' + self.uuid.hex + '_1')

    def test_two_namespace(self) -> None:
        '''torment.fixtures._unique_class_name({ 'f_{uuid}': None, 'f_{uuid}_1': None, }, uuid) == 'f_{uuid}_2' '''

        n = fixtures._unique_class_name({ 'f_' + self.uuid.hex: None, 'f_' + self.uuid.hex + '_1': None, }, self.uuid)

        self.assertEqual(n, 'f_' + self.uuid.hex + '_2')
