pyramid_traversalwrapper
========================

An alternate implementation of the
``pyramid.interfaces.ITraverserFactory`` (a "traverser") which
wraps each traversed object in a proxy.  This allows a
"location-ignorant" model (a model which does not possess intrinsic
``__name__`` and ``__parent__`` attributes) to be used as the root
object and as any object returned from any other model's
``__getitem__`` method during traversal.

See docs/index.rst for more information.

