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

import traceback
from threading import currentThread, Thread
import Queue

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ThreadedCommands(object):
    timeout = None
    def __init__(self, timeout):
        self.timeout = timeout
        self.qCommand = Queue.Queue()
        self.qResult = Queue.Queue()

        self._onIdle = []
        self._onClose = []

        t = Thread(target=self._t_process)
        self._thread = t

        t.setDaemon(True)
        t.start()

    def connect(self, onIdle, onClose):
        self._onIdle.append(onIdle)
        self._onClose.append(onClose)

    def disconnect(self, onIdle, onClose):
        self._onIdle.remove(onIdle)
        self._onClose.remove(onClose)

    def send(self, fn, *args, **kw):
        if currentThread() is self._thread:
            return fn(*args, **kw)

        self.qCommand.put((False, fn, args, kw))
        return None

    def call(self, fn, *args, **kw):
        if currentThread() is self._thread:
            return fn(*args, **kw)

        self.qCommand.put((True, fn, args, kw))

        complete, r = self.qResult.get()
        if not complete:
            raise r
        return r

    def close(self):
        if currentThread() is self._thread:
            raise RuntimeError("Do not close command queue within command queue")

        self.qCommand.put((True, None, None, None))
        complete, r = self.qResult.get()
        if not complete:
            raise r
        return r

    def _t_process(self):
        qCommand = self.qCommand
        qResult = self.qResult
        Empty = Queue.Empty
        while 1:
            try:
                isCall, fn, args, kw = qCommand.get(True, self.timeout)

            except Empty:
                self._t_idle()
                continue

            if fn is None:
                break

            try:
                r = fn(*args, **kw)
            except Exception, e:
                traceback.print_exc()
                print
                print
                if isCall: 
                    qResult.put((False, e))
            else:
                if isCall: 
                    qResult.put((True, r))

        self._t_close()
        if isCall: 
            qResult.put((True, None))

    def _t_idle(self):
        for fn in self._onIdle:
            fn()

    def _t_close(self):
        for fn in self._onClose:
            fn()
        self._thread = None

