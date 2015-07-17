.. title:: Torment

Torment
=======

Torment is scalable testing fixtures.

Getting Started
---------------

Torment gives you many options to generate fixtures to fit your testing needs.

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

Torment is based on a series of rules in order to work as expected.  Below you will find a short list of the minimum requirements required to get started.

1. A filename with the following format:  **[descriptive-statement]_{UUID}.py**
    
   * Where are these files located?
     
     * These can be located anywhere you would like.  In source, out of source, whatever you would like.  Normally alongside other tests. 

   * How do I load these files?

     * ``torment.helpers.import_directory``_ recursively loads python modules in a directory::
     
           helpers.import_directory(__name__, os.path.dirname(__file__))

2. Inside that newly created file, it must contain at least one register to build a testcase 
    
   * ``torment.fixtures.register``_ associates runtime with data, in other words it puts the data & class together

3. The register requires a FixtureClass (type is defined elsewhere)
    
   * What kind of class?
     
     * Must be a subclass of ``torment.fixtures.Fixture``_
   
   *  Where do I define it?

      * There is no restrctions on where you define.

4. A FixtureClass requires a TestContext
   
   * What goes into TestContext class, etc?
     
     * TestContext specifies which fixtures it should test::
           
           class HelperUnitTest(TestContext, metaclass = MetaContext):
               fixture_classes = (
                   ExtendFixture,
               )

   * Why do I have to set my metaclass to metacontext

     * The metacontext turns fixtures into test methods

.. note::
   A metaclass is the object that specifies how a class is created. 
   MetaContext is a metaclass we created to build TestContext classes.

   Before getting starting, if you are unfamiliar with metaclasses, it is highly recommended that you read the official Python documenation `here`_.  If you'd rather just review a quick, older primer, you can check out a 2012 `blog`_ from Jake Vanderplas.

.. _here: https://docs.python.org/3/reference/datamodel.html?highlight=metaclass#customizing-class-creation
.. _blog: https://jakevdp.github.io/blog/2012/12/01/a-primer-on-python-metaclasses/

.. toctree::
   :titlesonly:
   
   context
   fixtures

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
