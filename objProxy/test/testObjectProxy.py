#!/usr/bin/env python
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##~ Copyright (C) 2002-2004  TechGame Networks, LLC.
##~ 
##~ This library is free software; you can redistribute it and/or
##~ modify it under the terms of the BSD style License as found in the 
##~ LICENSE file included with this distribution.
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import unittest
import pickle
import weakref

from TG.objdbs.objProxy import ObjectProxy

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ExtendedObjectProxy(ObjectProxy):
    oid = 42
    def __proxy__(self):
        target = ObjectProxy.__proxy__(self)
        # you could do "whatever" you like here careful to remember that
        # besids "__dict__", variable access uses __proxy__ method you are
        # implementing
        if self.oid == 42:
            return target
        else:
            return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestClassic:
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    def __call__(self, value):
        return "special", value

class TestObject(object):
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    def __call__(self, value):
        return "special", value

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class VerifyMixin(object):
    def verifyBase(self, value):
        proxyValue = self.ProxyFactory(value)

        #~ identity ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.assert_(proxyValue is not value)
        self.assertNotEqual(id(proxyValue), id(value))

        #~ hash ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        try: 
            hash(value)
        except TypeError: 
            pass # unhashable
        else:
            self.assertEqual(hash(proxyValue), hash(value))

        #~ strings ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.assertNotEqual(repr(proxyValue), repr(value))
        self.assertEqual(str(proxyValue), str(value))
        self.assertEqual(unicode(proxyValue), unicode(value))

        self.verifyVars(value)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyWeakref(self, value):
        proxyValue = self.ProxyFactory(value)

        ref = weakref.ref(proxyValue)
        self.assertEqual(ref(), value)
        self.assertEqual(ref(), proxyValue.__getProxy__())
        self.assertEqual(ref(), proxyValue)

        # weakref.proxy is not compareable directly...
        proxy = weakref.proxy(proxyValue)
        self.assertEqual(str(proxy), str(value))
        self.assertEqual(str(proxy), str(proxyValue.__getProxy__()))
        self.assertEqual(str(proxy), str(proxyValue))


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyPickle(self, value):
        proxyValue = self.ProxyFactory(value)

        self.assertEqual(proxyValue.__getProxy__(), value)

        for protocol in xrange(pickle.HIGHEST_PROTOCOL, -1, -1):
            pickledTest = pickle.dumps(proxyValue, protocol)
            unpickledProxy = pickle.loads(pickledTest)

            self.assertEqual(unpickledProxy, value)
            self.assertEqual(unpickledProxy, proxyValue)
            self.assertEqual(unpickledProxy.__getProxy__(), value)
            self.assertEqual(unpickledProxy, proxyValue.__getProxy__())
            self.assertEqual(unpickledProxy.__getProxy__(), proxyValue.__getProxy__())


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyComparisons(self, value, smaller, greater):
        self.assert_(smaller <= value < greater, "verifyComparison arguments are invalid")

        proxyValue = self.ProxyFactory(value)

        #~ comparison ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.assertEqual(bool(proxyValue), bool(value))

        self.assert_(proxyValue == value)
        self.assert_(proxyValue <= value)
        self.assert_(proxyValue >= value)
        self.assert_(proxyValue != greater)
        self.assert_(proxyValue < greater)
        self.assert_(proxyValue <= greater)
        self.assert_(proxyValue >= smaller)

        if smaller is not value:
            self.assert_(proxyValue != smaller)
            self.assert_(proxyValue > smaller)

        #~ comparison, reverse ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.assert_(value == proxyValue)
        self.assert_(value <= proxyValue)
        self.assert_(value >= proxyValue)
        self.assert_(greater != proxyValue)
        self.assert_(greater > proxyValue)
        self.assert_(greater >= proxyValue)
        self.assert_(smaller <= proxyValue)
        if smaller is not value:
            self.assert_(smaller != proxyValue)
            self.assert_(smaller < proxyValue)

        #~ comparison, cmp ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.assertEqual(cmp(proxyValue, value), 0)
        self.assertEqual(cmp(value, proxyValue), 0)

        self.assertEqual(cmp(proxyValue, greater), -1)
        self.assertEqual(cmp(greater, proxyValue), 1)

        if smaller is not value:
            self.assertEqual(cmp(proxyValue, smaller), 1)
            self.assertEqual(cmp(smaller, proxyValue), -1)


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyAttributes(self, value, names='wilbur force fun'.split()):
        proxyValue = self.ProxyFactory(value)

        for name in names:
            self.assertEqual(hasattr(proxyValue, name), hasattr(value, name))
            if hasattr(value, name):
                self.assertEqual(getattr(proxyValue, name), getattr(value, name))

                setattr(proxyValue, name, name[::-1])
                self.assertEqual(getattr(proxyValue, name), name[::-1])

                delattr(proxyValue, name)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyNumeric(self, value, other):
        proxyValue = self.ProxyFactory(value)

        self.assertEqual(-proxyValue, -value)
        self.assertEqual(+proxyValue, +value)

        self.assertEqual(abs(proxyValue), abs(value))

        self.assertEqual(int(proxyValue), int(value))
        self.assertEqual(long(proxyValue), long(value))
        self.assertEqual(float(proxyValue), float(value))
        self.assertEqual(complex(proxyValue), complex(value))

        self.assertEqual(proxyValue + other, value + other)
        self.assertEqual(proxyValue - other, value - other)
        self.assertEqual(proxyValue * other, value * other)
        self.assertEqual(proxyValue / other, value / other)
        self.assertEqual(proxyValue // other, value // other)
        self.assertEqual(proxyValue % other, value % other)
        self.assertEqual(divmod(proxyValue, other), divmod(value, other))

        # reverse
        self.assertEqual(other + proxyValue, other + value)
        self.assertEqual(other - proxyValue, other - value)
        self.assertEqual(other * proxyValue, other * value)
        self.assertEqual(other / proxyValue, other / value)
        self.assertEqual(other // proxyValue, other // value)
        self.assertEqual(other % proxyValue, other % value)
        self.assertEqual(divmod(other, proxyValue), divmod(other, value))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyBitTwiddling(self, value, other):
        proxyValue = self.ProxyFactory(value)

        self.assertEqual(hex(proxyValue), hex(value))
        self.assertEqual(oct(proxyValue), oct(value))

        self.assertEqual(~proxyValue, ~value)
        self.assertEqual(proxyValue ** other, value ** other)
        self.assertEqual(proxyValue << other, value << other)
        self.assertEqual(proxyValue >> other, value >> other)
        self.assertEqual(proxyValue & other, value & other)
        self.assertEqual(proxyValue | other, value | other)
        self.assertEqual(proxyValue ^ other, value ^ other)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyMapping(self, valueCopy1, valueCopy2, element, index, readonly=False):
        self.assertEqual(valueCopy1, valueCopy2)
        proxyValue = self.ProxyFactory(valueCopy1)

        self.assertEqual(proxyValue, valueCopy2)
        self.assertEqual(len(proxyValue), len(valueCopy2))
        self.assertEqual(list(iter(proxyValue)), list(iter(valueCopy2)))

        self.assertEqual((element in proxyValue), (element in valueCopy2))
        self.assertEqual(proxyValue[index], valueCopy2[index])

        if readonly:
            return # the rest of this requires modifications

        valueCopy2[index] = "special"
        proxyValue[index] = "special"
        self.assertEqual(proxyValue, valueCopy2)
        self.assertEqual(proxyValue[index], valueCopy2[index])
        self.assertEqual(proxyValue[index], "special")
        self.assertEqual(valueCopy2[index], "special")

        del valueCopy2[index]
        del proxyValue[index]
        self.assertEqual(proxyValue, valueCopy2)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifySequence(self, valueCopy1, valueCopy2, index=2, indexEnd=-2, readonly=False):
        self.assertEqual(valueCopy1, valueCopy2)
        proxyValue = self.ProxyFactory(valueCopy1)

        self.assertEqual(proxyValue, valueCopy2)

        self.assertEqual(proxyValue[:], valueCopy2[:])
        self.assertEqual(proxyValue[index:], valueCopy2[index:])
        self.assertEqual(proxyValue[:indexEnd], valueCopy2[:indexEnd])
        self.assertEqual(proxyValue[index:indexEnd], valueCopy2[index:indexEnd])

        if readonly:
            return # the rest of this requires modifications

        replacement = range(len(valueCopy2[index:indexEnd]))
        proxyValue[index:indexEnd] = replacement
        valueCopy2[index:indexEnd] = replacement
        self.assertEqual(proxyValue, valueCopy2)

        del proxyValue[index:indexEnd]
        del valueCopy2[index:indexEnd]
        self.assertEqual(proxyValue, valueCopy2)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyVars(self, value):
        proxyValue = self.ProxyFactory(value)
        try:
            varsValue = vars(value)
        except TypeError:
            return

        varsProxy = vars(proxyValue)
        self.assertEqual(varsValue, varsProxy)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyCallable(self, value):
        proxyValue = self.ProxyFactory(value)
        self.assertEqual(proxyValue(42), ('special', 42))
        self.assertEqual(value(42), ('special', 42))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def verifyClassCallable(self, value):
        proxyValue = self.ProxyFactory(value)
        self.assert_(isinstance(value(), value))
        self.assert_(isinstance(proxyValue(), value))
        self.assertEqual(proxyValue(), value())

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestObjectProxies(unittest.TestCase, VerifyMixin):
    ProxyFactory = ObjectProxy

    def testNone(self):
        self.verifyBase(None)
        self.verifyWeakref(None)
        self.verifyPickle(None)
        self.verifyComparisons(None, None, 0)
        self.verifyAttributes(None)

    def test42(self):
        value = 42
        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyComparisons(value, 10, 50)
        self.verifyAttributes(value)
        self.verifyNumeric(value, 2)
        self.verifyBitTwiddling(value, 2)

    def test42Proxy(self):
        value = self.ProxyFactory(42)
        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyComparisons(value, 10, 50)
        self.verifyAttributes(value)
        self.verifyNumeric(value, 2)
        self.verifyBitTwiddling(value, 2)

    def test42Float(self):
        value = 42.0
        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyComparisons(value, 10.0, 50.0)
        self.verifyAttributes(value)
        self.verifyNumeric(value, 2.0)
        self.verifyNumeric(value, 2)

    def test42FloatProxy(self):
        value = self.ProxyFactory(42.0)
        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyComparisons(value, 10.0, 50.0)
        self.verifyAttributes(value)
        self.verifyNumeric(value, 2.0)
        self.verifyNumeric(value, 2)

    def testTuple(self):
        value = tuple(range(5))
        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyComparisons(value, value[:-1], value[1:])
        self.verifyAttributes(value)
        self.verifyMapping(value, value, 3, 2, readonly=True)
        self.verifyMapping(value, value, NotImplemented, -2, readonly=True)
        self.verifySequence(value, value, readonly=True)

    def testTupleProxy(self):
        value = self.ProxyFactory(tuple(range(5)))
        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyComparisons(value, value[:-1], value[1:])
        self.verifyAttributes(value)
        self.verifyMapping(value, value, 3, 2, readonly=True)
        self.verifyMapping(value, value, NotImplemented, -2, readonly=True)
        self.verifySequence(value, value, readonly=True)

    def testList(self):
        value = range(5)
        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyComparisons(value, value[:-1], value[1:])
        self.verifyAttributes(value)
        self.verifyMapping(value[:], value[:], 3, 2)
        self.verifyMapping(value[:], value[:], NotImplemented, -2)
        self.verifySequence(value[:], value[:])

        proxyValue = self.ProxyFactory(value)
        proxyValue.sort()

    def testDict(self):
        value = dict(zip(range(5), range(100,105)))
        less = value.copy()
        del less[0]
        more = value.copy()
        more[5] = 106
        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyComparisons(value, less, more)
        self.verifyAttributes(value)
        self.verifyMapping(value.copy(), value.copy(), 3, 4)
        self.verifyMapping(value.copy(), value.copy(), NotImplemented, 1)

        proxyValue = self.ProxyFactory(value)
        self.assertEqual(proxyValue.pop(2), 102)

    def testClassicClass(self):
        value = TestClassic
        value.wilbur = "was there"
        value.fun = "True"

        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyAttributes(value)
        self.verifyClassCallable(value)

    def testClassicInstance(self):
        value = TestClassic()
        value.wilbur = "was there"
        value.fun = "True"

        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyAttributes(value)
        self.verifyCallable(value)

    def testClass(self):
        value = TestObject
        value.wilbur = "was there"
        value.fun = "True"

        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyAttributes(value)
        self.verifyClassCallable(value)

    def testObject(self):
        value = TestObject()
        value.wilbur = "was there"
        value.fun = "True"

        self.verifyBase(value)
        self.verifyWeakref(value)
        self.verifyPickle(value)
        self.verifyAttributes(value)
        self.verifyCallable(value)

    def testDirectRecursive(self):
        proxyValue = self.ProxyFactory()
        proxyValue.__setProxy__(proxyValue)
        self.assertRaises(ValueError, repr, proxyValue)
    
    def testIndirectRecursive(self):
        proxyA = self.ProxyFactory()
        proxyB = self.ProxyFactory()
        proxyA.__setProxy__(proxyB)
        proxyB.__setProxy__(proxyA)
        self.assertRaises(ValueError, repr, proxyA)
        self.assertRaises(ValueError, repr, proxyB)
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestExtendedObjectProxies(TestObjectProxies):
    ProxyFactory = ExtendedObjectProxy

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Unittest Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__=='__main__':
    unittest.main()

