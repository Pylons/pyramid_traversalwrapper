pyramid_traversalwrapper
========================

An alternate implementation of the
``pyramid.interfaces.ITraverserFactory`` (a "traverser") which
wraps each traversed object in a proxy.  This allows a
"location-ignorant" model (a model which does not possess intrinsic
``__name__`` and ``__parent__`` attributes) to be used as the root
object and as any object returned from any other model's
``__getitem__`` method during traversal.

Installation
------------

Install using setuptools, e.g. (within a virtualenv)::

  $ easy_install pyramid_traversalwrapper

Usage
-----

When this ITraverserFactory is registered as the traverser for a Pyramid
application, during traversal, each object, including the root object is
wrapped in a proxy.  The proxy that provides the traversed object with a
``__name__`` and ``__parent__`` attribute.  The ``__name__`` and
``__parent__`` attributes of the root proxy are both ``None``.  The
``__name__`` of subsequently traversed object is the Unicode URL segment name
which was used to look it up.  The ``__parent__`` of subsequently traversed
objects is the previous object traversed.

In order to enable this package's ITraverserFactory, register the
``pyramid_traversalwrapper.ModelGraphTraverser`` as the traversal policy,
rather than the default ``ModelGraphTraverser``. To use this feature, your
application will need to have a dependency on this package, as well as
following stanza in its ``configure.zcml``::

    <adapter
        factory="pyramid_traversalwrapper.ModelGraphTraverser"
        provides="pyramid.interfaces.ITraverserFactory"
        for="*"
        />

.. note:: When this ITraverserFactory is used, the intrinsic
   ``__name__`` or ``__parent__`` attribute of an object are ignored.
   Even if an object in the graph (including the root objects) has an
   intrinsic ``__name__`` and ``__parent__`` attribute, it will still
   be wrapped in a proxy that override the object's "real"
   ``__parent__`` and ``__name__`` attributes.

Reporting Bugs / Development Versions
-------------------------------------

Visit https://github.com/Pylons/pyramid_traversalwrapper/issues to report
bugs.  Visit https://github.com/Pylons/pyramid_traversalwrapper to download
development or tagged versions.

Indices and tables
------------------

* :ref:`modindex`
* :ref:`search`
