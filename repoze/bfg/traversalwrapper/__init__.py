import zope.interface
from zope.interface import classProvides
from zope.interface import implements

from zope.proxy import ProxyBase, getProxiedObject, non_overridable
from zope.proxy.decorator import DecoratorSpecificationDescriptor

from repoze.bfg.interfaces import ILocation
from repoze.bfg.interfaces import ITraverser
from repoze.bfg.interfaces import ITraverserFactory
from repoze.bfg.interfaces import VH_ROOT_KEY

from repoze.bfg.traversal import traversal_path

_marker = object()

class ModelGraphTraverser(object):
    """ A model graph traverser that should be used (for convenience)
    when no object in the graph supplies either a ``__name__`` or a
    ``__parent__`` attribute (ie. no object 'provides the ILocation
    interface') ."""
    classProvides(ITraverserFactory)
    implements(ITraverser)
    def __init__(self, root):
        self.root = root

    def __call__(self, environ, _marker=_marker):
        try:
            path = environ['PATH_INFO']
        except KeyError:
            path = '/'
        try:
            vroot_path_string = environ[VH_ROOT_KEY]
        except KeyError:
            vroot_path = []
            vroot_idx = 0
        else:
            vroot_path = list(traversal_path(vroot_path_string))
            vroot_idx = len(vroot_path)
            path = vroot_path_string + path

        path = list(traversal_path(path))

        traversed = []

        ob = vroot = LocationProxy(self.root)
        name = ''

        i = 1

        for segment in path:
            if segment[:2] =='@@':
                return ob, segment[2:], path[i:], traversed, vroot, vroot_path
            try:
                getitem = ob.__getitem__
            except AttributeError:
                return ob, segment, path[i:], traversed, vroot, vroot_path
            try:
                next = getitem(segment)
            except KeyError:
                return ob, segment, path[i:], traversed, vroot, vroot_path
            next = LocationProxy(next, ob, segment)
            if vroot_idx == i-1:
                vroot = ob
            traversed.append(segment)
            ob = next
            i += 1

        return ob, '', [], traversed, vroot, vroot_path

class ClassAndInstanceDescr(object):

    def __init__(self, *args):
        self.funcs = args

    def __get__(self, inst, cls):
        if inst is None:
            return self.funcs[1](cls)
        return self.funcs[0](inst)

class LocationProxy(ProxyBase):
    """Location-object proxy

    This is a non-picklable proxy that can be put around objects that
    don't implement `ILocation`.
    """

    zope.interface.implements(ILocation)

    __slots__ = '__parent__', '__name__'
    __safe_for_unpickling__ = True

    def __new__(self, ob, container=None, name=None):
        return ProxyBase.__new__(self, ob)

    def __init__(self, ob, container=None, name=None):
        ProxyBase.__init__(self, ob)
        self.__parent__ = container
        self.__name__ = name

    @non_overridable
    def __reduce__(self, proto=None):
        raise TypeError("Not picklable")

    __doc__ = ClassAndInstanceDescr(
        lambda inst: getProxiedObject(inst).__doc__,
        lambda cls, __doc__ = __doc__: __doc__,
        )

    __reduce_ex__ = __reduce__

    __providedBy__ = DecoratorSpecificationDescriptor()

