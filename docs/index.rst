.. title:: Torment

Torment
=======

Torment is scalable testing fixtures.

Getting Started
---------------

Torment has many options to generate fixtures to fit your testing needs.

Multiple fixtures with the different data:

.. code-block:: python

    register(globals(), ( RequestFixture, ), {...})

Multiple fixtures using the same data (the runtime changes the behavior of the test):        

.. code-block:: python

    p = {...}
    
    register(globals(), ( WriteFixture, ), p)
    regsiter(globals(), ( ReadFixture, ), p)

Multiple fixtures using dynamic data:

.. code-block:: python

    for a in fixtures.of(( AccountModelFixture, )):
        register(globals(), ( RequestFixture, ), {
            'account': a,
        })

Torment Usage
^^^^^^^^^^^^^

In order to work as expected, Torment is based on a series of rules.  The minimum requirements to get started are listed below.

1. A filename with the following format:  **[descriptive-statement]_{UUID}.py**
    
   * Where are these files located?
     
     * These can be located anywhere you would like.  In source, out of source, whatever is desired.  Normally alongside other tests. 

   * How do I load these files?

     * ``torment.helpers.import_directory`` recursively loads python modules in a directory::
     
           helpers.import_directory(__name__, os.path.dirname(__file__))

2. The newly created file must contain at least one register to build a testcase
    
   * ``torment.fixtures.register`` associates runtime with data, in other words it puts the data & class together

3. The register requires a FixtureClass (type is defined elsewhere)
    
   * What kind of class?
     
     * Must be a subclass of ``torment.fixtures.Fixture``
   
   *  Where do I define it?

      * There are no restrictions on where you define

4. A FixtureClass requires a TestContext
   
   * What goes into TestContext class, etc?
     
     * TestContext specifies which fixtures it should test::
           
           class HelperUnitTest(TestContext, metaclass = contexts.MetaContext):
               fixture_classes = (
                   ExtendFixture,
               )

   * Why do I have to set my metaclass to metacontext?

     * The metacontext turns fixtures into test methods

.. note::
   A metaclass is the object that specifies how a class is created. 
   ``torment.contexts.MetaContext`` is a metaclass we created to build TestContext classes.

   If you are unfamiliar with metaclasses, it is highly recommended that you read the offical Python documentation  `here`_ before getting started.  For a quick primer refer to Jake Vanderplas'  `blog`_ post from 2012.  

.. _here: https://docs.python.org/3/reference/datamodel.html?highlight=metaclass#customizing-class-creation
.. _blog: https://jakevdp.github.io/blog/2012/12/01/a-primer-on-python-metaclasses/

.. toctree::
   :titlesonly:
   
   contexts
   fixtures

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
