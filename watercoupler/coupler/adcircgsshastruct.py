#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
from __future__ import absolute_import, print_function
import sys
import ctypes as ct

from pyADCIRC import pyadcirc as pa

import gsshapython.sclass.define_h      as gsshadefine
import gsshapython.sclass.fnctn_h       as gsshafnctn
import gsshapython.sclass.main_struct_h as gsshamain

################################################################################
TIME_TOL = 1.0E-3
SERIESLENGTH = 4 #This is the MINIMUM number of lines required in an ADCIRC series to be coupled. Compulsory.
GSSHA_TIME_FACTOR = 60.0 #Minutes to second conversion
GSSHA_CUFTPERSEC_TO_CUMPERSEC = 0.028316846592 # cu.ft/s to cu.m/s factor
DEBUG_LOCAL = 1

class adcircgsshastruct(): #Note: This is not a ctypes Structure!!!!
    def __init__(self):
        # Main ADCIRC and GSSHA structures
        self.pa    = pa
        self.ps    = pa.sizes
        self.pg    = pa.pyglobal
        self.pm    = pa.pymesh
        self.pmsg  = pa.pymessenger
        self.pb    = pa.pyboundaries
        self.pmain = pa.pyadcirc_mod
        self.pu    = pa.utilities
        self.mvs = gsshafnctn.get_lib_var(gsshafnctn.gsshalib,'python_main_var_struct_ptr', ct.POINTER(gsshamain.main_var_struct))
        # watercoupler data
        self.couplingtype = ''
        self.couplingntsteps = 1 #Number of ADCIRC time steps between coupled intervals; minimum = 1
        self.npes = 0
        self.myid = 0

        # ADCIRC data
        self.adcircrunflag=self.pu.on
        self.adcircdt=0.0
        self.adcircnt=0
        self.adcirctstart=0.0
        self.adcirctprev=0.0
        self.adcirctnext=0.0
        self.adcirctfinal=0.0
        self.adcircntsteps=0
        self.adcirc_comm_world=0
        self.adcirc_comm_comp=0

        self.adcircseries=0
        self.adcircedgestringid=self.pu.unset_int
        self.adcircedgestringnnodes=self.pu.unset_int
        self.adcircedgestringnodes=[]
        self.adcircedgestringlen=0.0
        self.adcircfort20pathname=''
        self.adcirc_hprev=0.0   # Avg depth
        self.adcirc_hprev_len=0.0   # count

        # GSSHA data
        self.gssharunflag=gsshadefine.ON
        self.gsshatstartjul=0.0
        self.gsshadt=0.0
        self.effectivegsshadt=0.0
        self.gsshatprev=0.0
        self.gsshatfinal=0.0
        self.gsshasingle_event_end=0.0
        self.gsshavoutprev=0.0
        self.gsshavoutprev_t=0.0
        self.gsshatimefact=GSSHA_TIME_FACTOR ## Minutes to seconds conversion, since niter is in mins.
        self.gsshahydrofact=1.0 # GSSHA_CUFTPERSEC_TO_CUMPERSEC may not be required after all since GSSHA internally seems to use cu.m/s.

    from ._coupler_initialize import adcircgssha_coupler_initialize as coupler_initialize
    from ._coupler_run import adcircgssha_coupler_run as coupler_run
    from ._coupler_finalize import adcircgssha_coupler_finalize as coupler_finalize


################################################################################
if __name__=='__main__':
    argv = ct.POINTER(ct.c_char_p)()
    argc = ct.c_int()
    ct.pythonapi.Py_GetArgcArgv(ct.byref(argc), ct.byref(argv))

    if DEBUG_LOCAL == 1:
        print('Number of arguments passed to python: {0} \nArgs:'.format(
            argc.value), end = '')
        [print(argv[i], end = ' ') for i in range(argc.value)]
        print()
    if argc.value>=6:
        print("ADCIRC project:", argv[argc.value-1])
        print("GSSHA project :", argv[argc.value-2])
        ags = adcircgsshastruct()
        ags.coupler_initialize(argc, argv)
        ags.coupler_run()
        ags.coupler_finalize()
    else:
        print("\nPath to ADCIRC and GSSHA input files not specified."
              "\nExiting without testing.")

