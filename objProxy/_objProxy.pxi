##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
##~ Copyright (C) 2002-2007  TechGame Networks, LLC.              ##
##~                                                               ##
##~ This library is free software; you can redistribute it        ##
##~ and/or modify it under the terms of the BSD style License as  ##
##~ found in the LICENSE file included with this distribution.    ##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Constants / Variables / Etc. 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__name__ = 'TG.objdbs.objProxy'

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cdef class IProxy:
    def __proxy__(self):
        """Should resolve the proxy object.  Default returns the "cached" proxy.  Override for different behavior"""
        raise NotImplementedError('__proxy__(): Subclass Responsibility')

    def __proxyOrNone__(self):
        """Should return proxy result, or None if the object doesn't need faulted in yet"""
        return self.__proxy__()

    def __repr__(self): 
        localClass = self.__localClass__()
        return "<%s.%s of %r>" % (localClass .__module__, localClass .__name__, self.__proxyOrNone__())

    def __localDict__(self):
        return IProxy.__getattribute__(self, '__dict__')
    def __localClass__(self):
        return IProxy.__getattribute__(self, '__class__')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cdef class ProxyBasic(IProxy):
    #~ hash ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __hash__(self): return hash(self.__proxy__())

    #~ strings ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __str__(self): return str(self.__proxy__())
    def __unicode__(self): return unicode(self.__proxy__())
            
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cdef class ProxyComparison(ProxyBasic):
    #~ comparison ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __nonzero__(self): return bool(self.__proxy__())

    def __eq__(self, other): 
        if isinstance(other, ProxyComparison):
            return self.__proxy__() == other.__proxy__()
        else:
            proxy = self.__proxy__()
            if proxy is other:
                return True
            return proxy == other

    def __ne__(self, other): 
        if isinstance(other, ProxyComparison):
            return self.__proxy__() <> other.__proxy__()
        else:
            proxy = self.__proxy__()
            if proxy is other:
                return False
            return self.__proxy__() <> other

    def __lt__(self, other): 
        if isinstance(other, ProxyComparison):
            return self.__proxy__() < other.__proxy__()
        else:
            return self.__proxy__() < other
    def __le__(self, other): 
        if isinstance(other, ProxyComparison):
            return self.__proxy__() <= other.__proxy__()
        else:
            return self.__proxy__() <= other
    def __gt__(self, other): 
        if isinstance(other, ProxyComparison):
            return self.__proxy__() > other.__proxy__()
        else:
            return self.__proxy__() > other
    def __ge__(self, other): 
        if isinstance(other, ProxyComparison):
            return self.__proxy__() >= other.__proxy__()
        else:
            return self.__proxy__() >= other

    def __cmp__(self, other): 
        if isinstance(other, ProxyComparison):
            return cmp(self.__proxy__(), other.__proxy__())
        else:
            return cmp(self.__proxy__(), other)

    def __rcmp__(self, other): 
        return cmp(other, self.__proxy__())

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cdef class ProxyAttributes(ProxyComparison):
    #~ attributes ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __getattr__(self, name): return getattr(self.__proxy__(), name)
    def __setattr__(self, name, value): setattr(self.__proxy__(), name, value)
    def __delattr__(self, name): delattr(self.__proxy__(), name)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cdef class NumericProxyBase(ProxyAttributes):
    #~ numeric, generic ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __neg__(self): return self.__proxy__().__neg__()
    def __pos__(self): return self.__proxy__().__pos__()
    def __abs__(self): return self.__proxy__().__abs__()

    def __index__(self): return self.__proxy__().__index__()
    def __int__(self): return int(self.__proxy__())
    def __long__(self): return long(self.__proxy__())
    def __float__(self): return float(self.__proxy__())
    def __complex__(self): return complex(self.__proxy__())

    def __oct__(self): return oct(self.__proxy__())
    def __hex__(self): return hex(self.__proxy__())

    def __coerce__(self, other): return coerce(self.__proxy__(), other)

    #~ numeric ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Note: apparently, when you over ride numeric operators at the class
    # level, the argument order can be switched on you...

    def __add__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__add__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__radd__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __sub__(self, other): 
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__sub__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rsub__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __mul__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__mul__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rmul__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __div__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__div__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rdiv__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __truediv__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__truediv__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rtruediv__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __floordiv__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__floordiv__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rfloordiv__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")

    def __mod__(self, other): 
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__mod__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rmod__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __divmod__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__divmod__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rdivmod__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __pow__(self, other, modulo): 
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__pow__(other, modulo)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rpow__(self, modulo)
        else: raise TypeError("Neither argument is a NumericProxy type")

    def __lshift__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__lshift__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rlshift__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __rshift__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__rshift__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rrshift__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")

    def __invert__(self): return self.__proxy__().__invert__()

    def __and__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__and__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rand__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __xor__(self, other):
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__xor__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__rxor__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")
    def __or__(self, other): 
        if isinstance(self, NumericProxyBase):
            return self.__proxy__().__or__(other)
        elif isinstance(other, NumericProxyBase):
            return other.__proxy__().__ror__(self)
        else: raise TypeError("Neither argument is a NumericProxy type")

    #~ numeric, reverse ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __radd__(self, other): return self.__proxy__().__radd__(other)
    def __rsub__(self, other): return self.__proxy__().__rsub__(other)
    def __rmul__(self, other): return self.__proxy__().__rmul__(other)
    def __rdiv__(self, other): return self.__proxy__().__rdiv__(other)
    def __rtruediv__(self, other): return self.__proxy__().__rtruediv__(other)
    def __rfloordiv__(self, other): return self.__proxy__().__rfloordiv__(other)
    def __rmod__(self, other): return self.__proxy__().__rmod__(other)
    def __rdivmod__(self, other): return self.__proxy__().__rdivmod__(other)
    def __rpow__(self, other, modulo): return self.__proxy__().__rpow__(other, modulo)
    def __rlshift__(self, other): return self.__proxy__().__rlshift__(other)
    def __rrshift__(self, other): return self.__proxy__().__rrshift__(other)
    def __rand__(self, other): return self.__proxy__().__rand__(other)
    def __rxor__(self, other): return self.__proxy__().__rxor__(other)
    def __ror__(self, other): return self.__proxy__().__ror__(other)

    #~ numeric, inplace ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __iadd__(self, other): return self.__proxy__().__iadd__(other)
    def __isub__(self, other): return self.__proxy__().__isub__(other)
    def __imul__(self, other): return self.__proxy__().__imul__(other)
    def __idiv__(self, other): return self.__proxy__().__idiv__(other)
    def __itruediv__(self, other): return self.__proxy__().__itruediv__(other)
    def __ifloordiv__(self, other): return self.__proxy__().__ifloordiv__(other)
    def __imod__(self, other): return self.__proxy__().__imod__(other)
    def __ipow__(self, other, modulo): return self.__proxy__().__ipow__(other, modulo)
    def __ilshift__(self, other): return self.__proxy__().__ilshift__(other)
    def __irshift__(self, other): return self.__proxy__().__irshift__(other)
    def __iand__(self, other): return self.__proxy__().__iand__(other)
    def __ixor__(self, other): return self.__proxy__().__ixor__(other)
    def __ior__(self, other): return self.__proxy__().__ior__(other)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cdef class MappingProxyBase(NumericProxyBase):
    #~ sequence/mapping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __len__(self): return self.__proxy__().__len__()

    def __contains__(self, key): return self.__proxy__().__contains__(key)
    def __getitem__(self, key): return self.__proxy__().__getitem__(key)
    def __setitem__(self, key, value): self.__proxy__().__setitem__(key, value)
    def __delitem__(self, key): self.__proxy__().__delitem__(key)

    def __iter__(self): return self.__proxy__().__iter__()

cdef class SequenceProxyBase(MappingProxyBase):
    #~ sequences ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __getslice__(self, i, j): return self.__proxy__().__getslice__(i, j)
    def __setslice__(self, i, j, sequence): self.__proxy__().__setslice__(i, j, sequence)
    def __delslice__(self, i, j): self.__proxy__().__delslice__(i, j)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ usable proxy classes
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def __newobj__(klass, *args):
    return klass.__new__(klass, *args)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cdef class ProxyBase(SequenceProxyBase):
    def __call__(self, *args, **kw): 
        return self.__proxy__()(*args, **kw)

cdef class Proxy(ProxyBase):
    cdef object proxy
    cdef int proxyRecursionLock

    def __init__(self, proxy=None):
        self.__setProxy__(proxy)

    def __proxyOrNone__(self):
        """Should return proxy result, or None if the object doesn't need faulted in yet"""
        return self.__proxy__()

    def __proxy__(self):
        target = self.__getProxy__()
        self.__check_recursive_proxy__(target)
        return target

    def __check_recursive_proxy__(self, target):
        """Should resolve the proxy object.  Default returns the "cached" proxy.  Override for different behavior"""
        if isinstance(target, IProxy):
            if self.proxyRecursionLock:
                raise ValueError("Self-referencing proxy!")

            self.proxyRecursionLock = 1
            target.__proxyOrNone__()
            self.proxyRecursionLock = 0

    def __getProxy__(self):
        return self.proxy
    def __setProxy__(self, proxy):
        self.proxy = proxy
        self.proxyRecursionLock = 0

    #~ pickle support ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __reduce_ex__(self, protocol):
        return __newobj__, (self.__localClass__(), ), self.__getstate__()

    def __getstate__(self):
        localDict = self.__localDict__().copy()
        localDict['proxy'] = self.__getProxy__()
        return localDict

    def __setstate__(self, state):
        self.__setProxy__(state.pop('proxy', None))
        self.__localDict__().update(state)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ProxyComplete(Proxy):
    __metaclass__ = type
    __module__ = __name__ # pyRex doesn't account for this properly... so trick it

    def __getattribute__(self, name):
        if name in ('__class__', '__dict__'):
            proxy = self.__proxyOrNone__()
            if proxy is not None:
                return getattr(proxy, name)
        return Proxy.__getattribute__(self, name)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjectProxy(Proxy):
    """End-use class
    
    Note the lack of cdef class -- that's important for some of the things
    to work above.  (like __eq__)
    """
    __metaclass__ = type
    __module__ = __name__ # pyRex doesn't account for this properly... so trick it

    def __getattribute__(self, name):
        if name in ('__dict__',):
            # This is not the whole truth of what's in the localDict, but we
            # are a proxy class.  So pretend like we are the remote class and
            # return it's dict.  If you really want this instance's dict, use
            # __localDict__()
            result = getattr(self.__proxy__(), name)
        else:
            result = Proxy.__getattribute__(self, name)
        return result

    def __getattr__(self, name):
        localDict = self.__localDict__()
        localClass = self.__localClass__()
        if (name in localDict) or (name in localClass.__dict__):
            # local vars
            result = ProxyBasic.__getattr__(self, name)
        else:
            result = Proxy.__getattr__(self, name)
        return result

    def __setattr__(self, name, value):
        localDict = self.__localDict__()
        localClass = self.__localClass__()
        if (name in localDict) or (name in localClass.__dict__):
            # local vars
            ProxyBasic.__setattr__(self, name, value)
        else:
            Proxy.__setattr__(self, name, value)

    def __delattr__(self, name):
        localDict = self.__localDict__()
        localClass = self.__localClass__()
        if (name in localDict) or (name in localClass.__dict__):
            # local vars
            ProxyBasic.__delattr__(self, name)
        else:
            Proxy.__delattr__(self, name)

