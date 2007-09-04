##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
##~ Copyright (C) 2002-2006  TechGame Networks, LLC.              ##
##~                                                               ##
##~ This library is free software; you can redistribute it        ##
##~ and/or modify it under the terms of the BSD style License as  ##
##~ found in the LICENSE file included with this distribution.    ##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os
from glob import iglob
import unittest

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Constants / Variables / Etc. 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pkgBaseTestPath = os.path.dirname(__file__) or os.getcwd()

if not os.path.isdir(pkgBaseTestPath):
    raise NotImplementedError("Running all tests from non-directory packages is not implemented")

else:
    # find the test modules using filesystem and globs
    def iterTestSuiteModules(testSuitePaths):
        for suiteCollection in testSuitePaths:
            for eachPath in suiteCollection:
                ppath, pbase = os.path.split(eachPath)
                if not pbase:
                    ppath, pbase = os.path.split(ppath)
                moduleName = os.path.splitext(pbase)[0]

                yield __import__(moduleName, globals())

    testSuiteModules = iterTestSuiteModules([
        iglob(os.path.join(pkgBaseTestPath, '*'+os.sep)),
        iglob(os.path.join(pkgBaseTestPath, 'test*.py')),
        ])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def loadTestSuite():
    def loadTestsFromModule(module, loadDefault=unittest.defaultTestLoader.loadTestsFromModule):
        loadTestSuite = getattr(module, 'loadTestSuite', None)
        if loadTestSuite is None:
            return loadDefault(module)
        return loadTestSuite()

    allSuites = unittest.TestSuite()
    for module in testSuiteModules:
        allSuites.addTest(loadTestsFromModule(module))

    return allSuites

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def main():
    return unittest.main(__name__, defaultTest='loadTestSuite')

if __name__=='__main__':
    main()

