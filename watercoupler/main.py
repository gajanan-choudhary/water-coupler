#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
"""
Main function of watercoupler, calling inititialize, run, and finalize.
"""

from __future__ import absolute_import, print_function
from sys import version_info as _version_info
import time
import ctypes as _ct

if (__package__ == 'watercoupler'):
    from . import watercoupler_path as _watercoupler_path
elif (__name__ == '__main__'):
    import watercoupler_path as _watercoupler_path
else:
    from . import watercoupler_path as _watercoupler_path

from watercoupler.coupler.adcircgsshastruct import  adcircgsshastruct

################################################################################
DEBUG_LOCAL = 1

__all__ = ['main'] # The only thing from this module to import if needed.

#------------------------------------------------------------------------------#
def _getargcargv():
    '''Get argc and argv into Python 2 or 3 version-independently.

    The Py_GetArgcArgv function returns argv[i] as c_wchar_p in Python 3x and
    c_char_p in Python 2x. We need them to be of type c_char_p since that is the
    correct equivalent to a NULL terminated string, char *, in C.
    '''

    argc = _ct.c_int()
    if (_version_info < (3, 0)):
        # Python 2x
        argv = _ct.POINTER(_ct.c_char_p)()
        _ct.pythonapi.Py_GetArgcArgv(_ct.byref(argc), _ct.byref(argv))
    else:
        # Python 3x
        argw = _ct.POINTER(_ct.c_wchar_p)()
        _ct.pythonapi.Py_GetArgcArgv(_ct.byref(argc), _ct.byref(argw))
        argv = (_ct.c_char_p*argc.value)()
        for i in range(argc.value):
            argv[i] = argw[i].encode()
        argv = _ct.cast(argv, _ct.POINTER(_ct.c_char_p))

    return argc, argv

################################################################################
def main():
    """Main function of watercoupler.

    Requires 4 command line arguments.
    The format is : python -m watercoupler \\
                        <coupled ADCIRC edge string ID> \\
                        <coupling type identifier> \\
                        <GSSHA project file name> \\
                        <ADCIRC input file names without extension>
    Coupling type identifier is one of: gdA, Adg, AdgdA, gdAdg.
    """

    argc, argv = _getargcargv()

    if (DEBUG_LOCAL == 1):
        print('Number of arguments passed to python: {0} \nArgs:'.format(
            argc.value), end = '')
        [print(argv[i], end = ' ') for i in range(argc.value)]
        print()
    if (_version_info < (3, 0)):
        couplingtype = argv[argc.value-3]
    else:
        couplingtype = str(argv[argc.value-3], 'utf-8')
    if (argc.value<6) or (couplingtype not in ['gdA', 'Adg', 'gdAdg', 'AdgdA']):
        print("\nProblem with command line arguments.")
        print("Format is : python -m watercoupler "
                "<coupled ADCIRC edge string ID> <coupling type> "
                "<GSSHA model> <ADCIRC model>")
        print("Coupling type options are: gdA, Adg, AdgdA, gdAdg")
        print("Exiting without testing.")
        return -1

    print("Coupling type :", argv[argc.value-3])
    print("ADCIRC project: {0}, coupled edge string ID {1}".format(
            argv[argc.value-1], argv[argc.value-4]))
    print("GSSHA project :", argv[argc.value-2])

    t0 = time.time()
    print("Initializing watercoupler")
    ags = adcircgsshastruct()
    ags.coupler_initialize(couplingtype, argc, argv)

    t1 = time.time()
    print("Running watercoupler")
    ags.coupler_run()

    t2 = time.time()
    print("Finalizing watercoupler")
    ags.coupler_finalize()

    t3 = time.time()

    tInit = t1-t0
    tRun = t2-t1
    tFin = t3-t2
    tTot = t3-t0

    print("Initialize time = {0}".format(tInit))
    print("Run time        = {0}".format(tRun))
    print("Finalize time   = {0}".format(tFin))
    print("Total time      = {0}".format(tTot))

    print("\nFinished running watercoupler")

    return 0

################################################################################
if __name__ == '__main__':
    main()
