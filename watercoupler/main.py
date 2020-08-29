#!/usr/bin/env python
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
"""
Main function of watercoupler, calling inititialize, run, and finalize.
"""

import time
import ctypes as ct

import watercoupler_path
from coupler.adcircgsshastruct import  adcircgsshastruct

################################################################################
DEBUG_LOCAL = 1

__all__ = ['main'] # The only thing from this module to import if needed.

################################################################################
def main():
    """Main function of watercoupler.

    Requires 4 command line arguments.
    The format is : python watercoupler.py \\
                        <coupled ADCIRC edge string ID> \\
                        <coupling type identifier> \\
                        <GSSHA project file name> \\
                        <ADCIRC input file names without extension>
    Coupling type identifier is one of: gdA, Adg, AdgdA, gdAdg
    """

    argv = ct.POINTER(ct.c_char_p)()
    argc = ct.c_int()
    ct.pythonapi.Py_GetArgcArgv(ct.byref(argc), ct.byref(argv))

    if DEBUG_LOCAL == 1:
        print 'Number of arguments passed to python:', argc.value, '\nArgs:',
        for i in range(argc.value):
            print argv[i],
        print
    if (argc.value<6) or (argv[argc.value-3] not in ['gdA', 'Adg', 'gdAdg', 'AdgdA']):
        print "\nProblem with command line arguments."
        print "Format is : python <*.py> <coupled ADCIRC edge string ID> <coupling type> <GSSHA model> <ADCIRC model>"
        print "Coupling type options are: gdA, Adg, AdgdA, gdAdg"
        print "Exiting without testing."
        return -1

    print "Coupling type :", argv[argc.value-3]
    print "ADCIRC project:", argv[argc.value-1], ", coupled edge string ID", argv[argc.value-4]
    print "GSSHA project :", argv[argc.value-2]

    t0 = time.time()
    print("Initializing watercoupler")
    ags = adcircgsshastruct()
    ags.coupler_initialize(argc, argv)

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
