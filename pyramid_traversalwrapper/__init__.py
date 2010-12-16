import zope.interface
from zope.interface import classProvides
from zope.interface import implements

from zope.proxy import ProxyBase, getProxiedObject, non_overridable
from zope.proxy.decorator import DecoratorSpecificationDescriptor

from pyramid.interfaces import ILocation
from pyramid.interfaces import ITraverser
from pyramid.interfaces import ITraverserFactory
from pyramid.interfaces import VH_ROOT_KEY

from pyramid.traversal import traversal_path

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

    def __call__(self, environ):
        if 'bfg.routes.matchdict' in environ:
            matchdict = environ['bfg.routes.matchdict']
            path = matchdict.get('traverse', '/')
            subpath = matchdict.get('subpath', '')
            subpath = tuple(filter(None, subpath.split('/')))
        else:
            # this request did not match a Routes route
            subpath = ()
            try:
                path = environ['PATH_INFO'] or '/'
            except KeyError:
                path = '/'

        try:
            vroot_path = environ[VH_ROOT_KEY]
        except KeyError:
            vroot_tuple = ()
            vpath = path
            vroot_idx = -1
        else:
            vroot_tuple = traversal_path(vroot_path)
            vpath = vroot_path + path
            vroot_idx = len(vroot_tuple) -1

        ob = vroot = LocationProxy(self.root)

        if vpath == '/' or (not vpath):
            # prevent a call to traversal_path if we know it's going
            # to return the empty tuple
            vpath_tuple = ()
        else:
            # we do dead reckoning here via tuple slicing instead of
            # pushing and popping temporary lists for speed purposes
            # and this hurts readability; apologies
            i = 0
            vpath_tuple = traversal_path(vpath)
            for segment in vpath_tuple:
                if segment[:2] =='@@':
                    return dict(context=ob, view_name=segment[2:],
                                subpath=vpath_tuple[i+1:],
                                traversed=vpath_tuple[:vroot_idx+i+1],
                                virtual_root=vroot,
                                virtual_root_path=vroot_tuple,
                                root=self.root)
                try:
                    getitem = ob.__getitem__
                except AttributeError:
                    return dict(context=ob, view_name=segment,
                                subpath=vpath_tuple[i+1:],
                                traversed=vpath_tuple[:vroot_idx+i+1],
                                virtual_root=vroot,
                                virtual_root_path=vroot_tuple,
                                root=self.root)

                try:
                    next = getitem(segment)
                except KeyError:
                    return dict(context=ob, view_name=segment,
                                subpath=vpath_tuple[i+1:],
                                traversed=vpath_tuple[:vroot_idx+i+1],
                                virtual_root=vroot,
                                virtual_root_path=vroot_tuple,
                                root=self.root)
                next = LocationProxy(next, ob, segment)
                if i == vroot_idx: 
                    vroot = next
                ob = next
                i += 1

        return dict(context=ob, view_name=u'', subpath=subpath,
                    traversed=vpath_tuple, virtual_root=vroot,
                    virtual_root_path=vroot_tuple, root=self.root)

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

