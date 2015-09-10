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
import os
import sys
import typing  # noqa (use mypy typing)
import uuid

from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Tuple
from typing import Union

from torment import decorators

logger = logging.getLogger(__name__)


class Fixture(object):
    '''Collection of data and actions for a particular test case.

    Intended as a base class for custom fixtures.  Fixture provides an API
    that simplifies writing scalable test cases.

    Creating Fixture objects is broken into two parts.  This keeps the logic for
    a class of test cases separate from the data for particular cases while
    allowing re-use of the data provided by a fixture.

    The first part of Fixture object creation is crafting a proper subclass that
    implements the necessary actions:

    :``__init__``:   pre-data population initialization
    :``initialize``: post-data population initialization
    :``setup``:      pre-run setup
    :``run``:        REQUIRED—run code under test
    :``check``:      verify results of run

    .. note::
        ``initialize`` is run during ``__init__`` and setup is run after;
        otherwise, they serve the same function.  The split allows different
        actions to occur in different areas of the class heirarchy and generally
        isn't necessary.

    By default all actions are noops and simply do nothing but run is required.
    These actions allow complex class hierarchies to provide nuanced testing
    behavior.  For example, Fixture provides the absolute bare minimum to test
    any Fixture and no more.  By adding a set of subclasses, common
    initialization and checks can be performed at one layer while specific run
    decisions and checks can happen at a lower layer.

    The second part of Fixture object creation is crafting the data.  Tying data
    to a Fixture class should be done with ``torment.fixtures.register``.  It
    provides a declarative interface that binds a dictionary to a Fixture (keys
    of dictionary become Fixture properties).  ``torment.fixtures.register``
    creates a subclass that the rest of the torment knows how to transform into
    test cases that are compatible with nose.

    **Examples**

    Simplest Fixture subclass:

    .. code-block:: python

       class MyFixture(Fixture):
           pass

    Of course, to be useful the Fixture needs definitions of setup, run, and
    check that actually test the code we're interested in checking:

    .. code-block:: python

       def add(x, y):
           return x + y

       class AddFixture(Fixture):
           def run(self):
               self.result = add(self.parameters['x'], self.parameters['y'])

           def check(self):
               self.context.assertEqual(self.result, self.expected)

    This fixture uses a couple of conventions (not requirements):

    #. ``self.parameters`` as a dictionary of parameter names to values
    #. ``self.expected`` as the value we expect as a result
    #. ``self.result`` as the holder inside the fixture between ``run`` and
       ``check``

    This show-cases the ridiculity of using this testing framework for simple
    functions that have few cases that require testing.  This framework is
    designed to allow many cases to be easily and declaritively defined.

    The last component required to get these fixtures to actually run is hooking
    them together with a context:

    .. code-block:: python

       from torment import contexts

       class AddUnitTest(contexts.TestContext, metaclass = contexts.MetaContext):
           fixture_classes = (
               MyFixture,
               AddFixture,
           )

    The context that wraps a Fixture subclass should eventually inherit from
    TestContext (which inherits from ``unittest.TestCase`` and provides its assert
    methods).  In order for nose to find and execute this ``TestContext``, it
    must have a name that contains Test.

    **Properties**

    * ``category``
    * ``description`` (override)
    * ``name`` (do **not** override)

    **Methods To Override**

    * ``__init__``
    * ``check``
    * ``initialize``
    * ``run (required)``
    * ``setup``

    **Instance Variables**

    :``context``: the ``torment.TestContext`` this case is running in which
                  provides the assertion methods of ``unittest.TestCase``.

    '''

    def __init__(self, context: 'torment.TestContext') -> None:
        '''Create Fixture

        Initializes the Fixture's context (can be changed like any other
        property).

        **Parameters**

        :``context``: a subclass of ``torment.TestContext`` that provides
                      assertion methods and any other environmental information
                      for this test case

        '''

        self.context = context

    @property
    def category(self) -> str:
        '''Fixture's category (the containing testing module name)

        **Examples**

        :module:   test_torment.test_unit.test_fixtures.fixture_a44bc6dda6654b1395a8c2cbd55d964d
        :category: fixtures

        '''

        logger.debug('dir(self.__module__): %s', dir(self.__module__))

        return self.__module__.__name__.rsplit('.', 2)[-2].replace('test_', '')

    @property
    def description(self) -> str:
        '''Test name in nose output (intended to be overridden).'''

        return '{0.uuid.hex}—{1}'.format(self, self.context.module)

    @property
    def name(self) -> str:
        '''Method name in nose runtime.'''

        return 'test_' + self.__class__.__name__

    def initialize(self) -> None:
        '''Post-data population initialization hook.

        .. note::
            Override as necessary.  Default provided so re-defenition is not
            necessary.

        Called during ``__init__`` and after properties have been populated by
        ``torment.fixtures.register``.


        '''

        pass

    def setup(self) -> None:
        '''Pre-run initialization hook.

        .. note::
            Override as necessary.  Default provided so re-defenition is not
            necessary.

        Called after properties have been populated by
        ``torment.fixtures.register``.

        '''

        pass

    def check(self) -> None:
        '''Check that run ran as expected.

        .. note::
            Override as necessary.  Default provided so re-defenition is not
            necessary.

        Called after ``run`` and should be used to verify that run performed the
        expected actions.

        '''

        pass

    def _execute(self) -> None:
        '''Run Fixture actions (setup, run, check).

        Core test loop for Fixture.  Executes setup, run, and check in order.

        '''

        if hasattr(self, '_last_resolver_exception'):
            logger.warning('last exception from %s.%s:', self.__class__.__name__, self._last_resolver_exception[0], exc_info = self._last_resolver_exception[1])

        self.setup()
        self.run()
        self.check()


@decorators.log
def of(fixture_classes: Iterable[type], context: Union[None, 'torment.TestContext'] = None) -> Iterable['torment.fixtures.Fixture']:
    '''Obtain all Fixture objects of the provided classes.

    **Parameters**

    :``fixture_classes``: classes inheriting from ``torment.fixtures.Fixture``
    :``context``:         a ``torment.TestContext`` to initialize Fixtures with

    **Return Value(s)**

    Instantiated ``torment.fixtures.Fixture`` objects for each individual
    fixture class that inherits from one of the provided classes.

    '''

    classes = list(copy.copy(fixture_classes))
    fixtures = []  # type: Iterable[torment.fixtures.Fixture]

    while len(classes):
        current = classes.pop()
        subclasses = current.__subclasses__()

        if len(subclasses):
            classes.extend(subclasses)
        elif current not in fixture_classes:
            fixtures.append(current(context))

    return fixtures


def register(namespace, base_classes: Tuple[type], properties: Dict[str, Any]) -> None:
    '''Register a Fixture class in namespace with the given properties.

    Creates a Fixture class (not object) and inserts it into the provided
    namespace.  The properties is a dict but allows functions to reference other
    properties and acts like a small DSL (domain specific language).  This is
    really just a declarative way to compose data about a test fixture and make
    it repeatable.

    Files calling this function are expected to house one or more Fixtures and
    have a name that ends with a UUID without its hyphens.  For example:
    foo_38de9ceec5694c96ace90c9ca37e5bcb.py.  This UUID is used to uniquely
    track the Fixture through the test suite and allow Fixtures to scale without
    concern.

    **Parameters**

    :``namespace``:    dictionary to insert the generated class into
    :``base_classes``: list of classes the new class should inherit
    :``properties``:   dictionary of properties with their values

    Properties can have the following forms:

    :functions: invoked with the Fixture as it's argument
    :classes:   instantiated without any arguments (unless it subclasses
                ``torment.fixtures.Fixture`` in which case it's passed context)
    :literals:  any standard python type (i.e. int, str, dict)

    .. note::
        function execution may error (this will be emitted as a logging event).
        functions will continually be tried until they resolve or the same set
        of functions is continually erroring.  These functions that failed to
        resolve are left in tact for later processing.

    Properties by the following names also have defined behavior:

    :description: added to the Fixture's description as an addendum
    :error:       must be a dictionary with three keys:
                  :class:  class to instantiate (usually an exception)
                  :args:   arguments to pass to class initialization
                  :kwargs: keyword arguments to pass to class initialization

    Properties by the following names are reserved and should not be used:

    * name

    '''

    # ensure we have a clean copy of the data
    # and won't stomp on re-uses elsewhere in
    # someone's code
    props = copy.deepcopy(properties)

    desc = props.pop('description', None)  # type: Union[str, None]

    caller_frame = inspect.stack()[1]

    caller_file = caller_frame[1]
    caller_module = inspect.getmodule(caller_frame[0])

    my_uuid = uuid.UUID(os.path.basename(caller_file).replace('.py', '').rsplit('_', 1)[-1])
    class_name = _unique_class_name(namespace, my_uuid)

    @property
    def description(self) -> str:
        _ = super(self.__class__, self).description

        if desc is not None:
            _ += '—' + desc

        return _

    def __init__(self, context: 'torment.TestContext') -> None:
        super(self.__class__, self).__init__(context)

        functions = {}

        for name, value in props.items():
            if name == 'error':
                self.error = value['class'](*value.get('args', ()), **value.get('kwargs', {}))
                continue

            if inspect.isclass(value):
                if issubclass(value, Fixture):
                    value = value(self.context)
                else:
                    value = value()

            if inspect.isfunction(value):
                functions[name] = value
                continue

            setattr(self, name, value)

        _resolve_functions(functions, self)

        self.initialize()

    namespace[class_name] = type(class_name, base_classes, {
        'description': description,
        '__init__': __init__,
        '__module__': caller_module,
        'uuid': my_uuid,
    })


def _resolve_functions(functions: Dict[str, Callable[[Any], Any]], fixture: Fixture) -> None:
        '''Apply functions and collect values as properties on fixture.

        Call functions and apply their values as properteis on fixture.
        Functions will continue to get applied until no more functions resolve.
        All unresolved functions are logged and the last exception to have
        occurred is also logged.  This function does not return but adds the
        results to fixture directly.

        **Parameters**

        :``functions``: dict mapping function names (property names) to
                        callable functions
        :``fixture``:   Fixture to add values to

        '''

        exc_info = last_function = None
        function_count = float('inf')

        while function_count > len(functions):
            function_count = len(functions)

            for name, function in copy.copy(functions).items():
                try:
                    setattr(fixture, name, copy.deepcopy(function(fixture)))
                    del functions[name]
                except:
                    exc_info = sys.exc_info()

                    logger.debug('name: %s', name)
                    logger.debug('exc_info: %s', exc_info)

                    last_function = name

        if len(functions):
            logger.warning('unprocessed Fixture properties: %s', ','.join(functions.keys()))
            logger.warning('last exception from %s.%s:', fixture.name, last_function, exc_info = exc_info)

            setattr(fixture, '_last_resolver_exception', ( last_function, exc_info, ))

            for name, function in copy.copy(functions).items():
                setattr(fixture, name, function)


def _unique_class_name(namespace: Dict[str, Any], uuid: uuid.UUID) -> str:
    '''Generate unique to namespace name for a class using uuid.

    **Parameters**

    :``namespace``: the namespace to verify uniqueness against
    :``uuid``:      the "unique" portion of the name

    **Return Value(s)**

    A unique string (in namespace) using uuid.

    '''

    count = 0

    name = original_name = 'f_' + uuid.hex
    while name in namespace:
        count += 1
        name = original_name + '_' + str(count)

    return name
