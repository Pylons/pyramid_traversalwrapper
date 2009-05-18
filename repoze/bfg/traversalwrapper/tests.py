import unittest
from zope.testing.cleanup import cleanUp

class ModelGraphTraverserTests(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()
        
    def _getTargetClass(self):
        from repoze.bfg.traversalwrapper import ModelGraphTraverser
        return ModelGraphTraverser

    def _makeOne(self, *arg, **kw):
        klass = self._getTargetClass()
        return klass(*arg, **kw)

    def _getEnviron(self, **kw):
        environ = {}
        environ.update(kw)
        return environ

    def test_class_conforms_to_ITraverser(self):
        from zope.interface.verify import verifyClass
        from repoze.bfg.interfaces import ITraverser
        verifyClass(ITraverser, self._getTargetClass())

    def test_instance_conforms_to_ITraverser(self):
        from zope.interface.verify import verifyObject
        from repoze.bfg.interfaces import ITraverser
        context = DummyContext()
        verifyObject(ITraverser, self._makeOne(context))

    def test_call_with_no_pathinfo(self):
        policy = self._makeOne(None)
        environ = self._getEnviron()
        result = policy(environ)
        self.assertEqual(result['context'], None)
        self.assertEqual(result['view_name'], '')
        self.assertEqual(result['subpath'], [])
        self.assertEqual(result['traversed'], [])
        self.assertEqual(result['root'], policy.root)
        self.assertEqual(result['vroot'], policy.root)
        self.assertEqual(result['vroot_path'], [])

    def test_call_pathel_with_no_getitem(self):
        policy = self._makeOne(None)
        environ = self._getEnviron(PATH_INFO='/foo/bar')
        result = policy(environ)
        self.assertEqual(result['context'], None)
        self.assertEqual(result['view_name'], 'foo')
        self.assertEqual(result['subpath'], ['bar'])
        self.assertEqual(result['traversed'], [])
        self.assertEqual(result['root'], policy.root)
        self.assertEqual(result['vroot'], policy.root)
        self.assertEqual(result['vroot_path'], [])

    def test_call_withconn_getitem_emptypath_nosubpath(self):
        root = DummyContext()
        policy = self._makeOne(root)
        environ = self._getEnviron(PATH_INFO='')
        result = policy(environ)
        self.assertEqual(result['context'], root)
        self.assertEqual(result['view_name'], '')
        self.assertEqual(result['subpath'], [])
        self.assertEqual(result['traversed'], [])
        self.assertEqual(result['root'], root)
        self.assertEqual(result['vroot'], root)
        self.assertEqual(result['vroot_path'], [])

    def test_call_withconn_getitem_withpath_nosubpath(self):
        foo = DummyContext()
        root = DummyContext(foo)
        policy = self._makeOne(root)
        environ = self._getEnviron(PATH_INFO='/foo/bar')
        result = policy(environ)
        self.assertEqual(result['context'], foo)
        self.assertEqual(result['view_name'], 'bar')
        self.assertEqual(result['subpath'], [])
        self.assertEqual(result['traversed'], [u'foo'])
        self.assertEqual(result['root'], root)
        self.assertEqual(result['vroot'], root)
        self.assertEqual(result['vroot_path'], [])

    def test_call_withconn_getitem_withpath_withsubpath(self):
        foo = DummyContext()
        root = DummyContext(foo)
        policy = self._makeOne(root)
        environ = self._getEnviron(PATH_INFO='/foo/bar/baz/buz')
        result = policy(environ)
        self.assertEqual(result['context'], foo)
        self.assertEqual(result['view_name'], 'bar')
        self.assertEqual(result['subpath'], ['baz', 'buz'])
        self.assertEqual(result['traversed'], [u'foo'])
        self.assertEqual(result['root'], root)
        self.assertEqual(result['vroot'], root)
        self.assertEqual(result['vroot_path'], [])

    def test_call_with_explicit_viewname(self):
        foo = DummyContext()
        root = DummyContext(foo)
        policy = self._makeOne(root)
        environ = self._getEnviron(PATH_INFO='/@@foo')
        result = policy(environ)
        self.assertEqual(result['context'], root)
        self.assertEqual(result['view_name'], 'foo')
        self.assertEqual(result['subpath'], [])
        self.assertEqual(result['traversed'], [])
        self.assertEqual(result['root'], root)
        self.assertEqual(result['vroot'], root)
        self.assertEqual(result['vroot_path'], [])

    def test_call_with_vh_root(self):
        environ = self._getEnviron(PATH_INFO='/baz',
                                   HTTP_X_VHM_ROOT='/foo/bar')
        baz = DummyContext()
        baz.name = 'baz'
        bar = DummyContext(baz)
        bar.name = 'bar'
        foo = DummyContext(bar)
        foo.name = 'foo'
        root = DummyContext(foo)
        root.name = 'root'
        policy = self._makeOne(root)
        result = policy(environ)
        self.assertEqual(result['context'], baz)
        self.assertEqual(result['view_name'], '')
        self.assertEqual(result['subpath'], [])
        self.assertEqual(result['traversed'], [u'foo', u'bar', u'baz'])
        self.assertEqual(result['root'], root)
        self.assertEqual(result['vroot'], bar)
        self.assertEqual(result['vroot_path'], [u'foo', u'bar'])

    def test_non_utf8_path_segment_unicode_path_segments_fails(self):
        foo = DummyContext()
        root = DummyContext(foo)
        policy = self._makeOne(root)
        segment = unicode('LaPe\xc3\xb1a', 'utf-8').encode('utf-16')
        environ = self._getEnviron(PATH_INFO='/%s' % segment)
        self.assertRaises(TypeError, policy, environ)

    def test_non_utf8_path_segment_settings_unicode_path_segments_fails(self):
        foo = DummyContext()
        root = DummyContext(foo)
        policy = self._makeOne(root)
        segment = unicode('LaPe\xc3\xb1a', 'utf-8').encode('utf-16')
        environ = self._getEnviron(PATH_INFO='/%s' % segment)
        self.assertRaises(TypeError, policy, environ)

    def test_call_proxies(self):
        baz = DummyContext()
        bar = DummyContext(baz)
        foo = DummyContext(bar)
        root = DummyContext(foo)
        from zope.proxy import isProxy
        policy = self._makeOne(root)
        environ = self._getEnviron(PATH_INFO='/foo/bar/baz')
        result = policy(environ)
        ctx, name, subpath, traversed, vroot, vroot_path = (
            result['context'], result['view_name'], result['subpath'],
            result['traversed'], result['vroot'], result['vroot_path'])
        self.assertEqual(name, '')
        self.assertEqual(subpath, [])
        self.assertEqual(ctx, baz)
        self.failUnless(isProxy(ctx))
        self.assertEqual(ctx.__name__, 'baz')
        self.assertEqual(ctx.__parent__, bar)
        self.failUnless(isProxy(ctx.__parent__))
        self.assertEqual(ctx.__parent__.__name__, 'bar')
        self.assertEqual(ctx.__parent__.__parent__, foo)
        self.failUnless(isProxy(ctx.__parent__.__parent__))
        self.assertEqual(ctx.__parent__.__parent__.__name__, 'foo')
        self.assertEqual(ctx.__parent__.__parent__.__parent__, root)
        self.failUnless(isProxy(ctx.__parent__.__parent__.__parent__))
        self.assertEqual(ctx.__parent__.__parent__.__parent__.__name__, None)
        self.assertEqual(ctx.__parent__.__parent__.__parent__.__parent__, None)
        self.assertEqual(traversed, [u'foo', u'bar', u'baz'])
        self.assertEqual(vroot, root)
        self.assertEqual(vroot_path, [])

class TestLocationProxy(unittest.TestCase):

    def test_it(self):
        from repoze.bfg.traversalwrapper import LocationProxy
        from repoze.bfg.interfaces import ILocation
        l = [1, 2, 3]
        self.assertEqual(ILocation.providedBy(l), False)
        p = LocationProxy(l, "Dad", "p")
        self.assertEqual(p, [1, 2, 3])
        self.assertEqual(ILocation.providedBy(p), True)
        self.assertEqual(p.__parent__, 'Dad')
        self.assertEqual(p.__name__, 'p')
        import pickle
        self.assertRaises(TypeError, pickle.dumps, p)
        # Proxies should get their doc strings from the object they proxy:
        self.assertEqual(p.__doc__, l.__doc__)

class TestClassAndInstanceDescr(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.bfg.traversalwrapper import ClassAndInstanceDescr
        return ClassAndInstanceDescr

    def _makeOne(self, *arg):
        return self._getTargetClass()(*arg)

    def test__get__noinst(self):
        def f(ob):
            return ob
        ob = self._makeOne(f, f)
        result = ob.__get__(None, 1)
        self.assertEqual(result, 1)
    
    def test__get__withinst(self):
        def f(ob):
            return ob
        ob = self._makeOne(f, f)
        result = ob.__get__(1, 2)
        self.assertEqual(result, 1)


class DummyContext(object):
    __parent__ = None
    __name__ = None
    def __init__(self, next=None):
        self.next = next
        
    def __getitem__(self, name):
        if self.next is None:
            raise KeyError, name
        return self.next

