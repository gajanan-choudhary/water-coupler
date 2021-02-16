#!/usr/bin/env python
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#

import numpy as np
from ctypes import byref as ctypes_byref

DEBUG_LOCAL = 0

################################################################################
def adcircgssha_coupler_initialize(self, argc, argv):
    # argv[argc-1] must be ADCIRC model
    # argv[argc-2] must by GSSHA model
    # argv[argc-3] must be coupling type: 'gda', 'adg', 'gdadg', 'adgda'
    # argv[argc-4] must be edge string ID of the ADCIRC model that we are coupling to

    ######################################################
    import pyadcirc as pa
    ps    = pa.sizes
    pg    = pa.pyglobal
    pm    = pa.pymesh
    pmsg  = pa.pymessenger
    pb    = pa.pyboundaries
    pmain = pa.pyadcirc_mod
    pu    = pa.utilities

    ######################################################
    import gsshapython.sclass.build_options as gsshaopts
    import gsshapython.sclass.define_h      as gsshadefine
    import gsshapython.sclass.fnctn_h       as gsshafnctn

    ######################################################
    #SET UP ADCIRC.
    ######################################################
    if pu.debug == pu.on and DEBUG_LOCAL != 0:
        print("\nInitializing ADCIRC\n")
    self.pmain.pyadcirc_init()
    self.npes = self.ps.mnproc
    self.myid = self.ps.myproc
    if self.pu.messg == self.pu.on:
        self.adcirc_comm_world = pmsg.mpi_comm_adcirc
        self.adcirc_comm_comp = pg.comm
    if pu.debug == pu.on and DEBUG_LOCAL != 0:
        print("MPI Info: npes =", self.npes, ", myid =", self.myid)

    ######################################################
    if pu.messg == pu.on:
        #self.pmsg.msg_init()
        if (pu.debug == pu.on and DEBUG_LOCAL!=0):
            print('Python: adcirc_comm_world pointer value         : '+hex(self.adcirc_comm_world))
            print('Python: adcirc_comm_comp  pointer value         : '+hex(self.adcirc_comm_comp))
        print("*********************** MPI Initialized ***********************")
        print("***************************************************************")


    print("********************* ADCIRC Initialized **********************")
    print("***************************************************************")

    ######################################################
    #SET UP GSSHA.
    ######################################################
    if gsshaopts._DEBUG == gsshadefine.ON and DEBUG_LOCAL != 0:
        print "\nInitializing GSSHA\n"
    prj_name = argv[argc.value-2]
    ierr_code = gsshafnctn.main_gssha_initialize(ctypes_byref(self.mvs), prj_name, None, prj_name)
    assert(ierr_code == 0) #Since sm is not NULL now
    print "********************** GSSHA Initialized **********************"
    print "***************************************************************"

    ######################################################
    #SET UP COUPLED STRUCT.
    ######################################################
    self.couplingtype=argv[argc.value-3]
    #self.couplingdtfactor = 480 #in case of original Gal-brays-coupling
    self.adcircrunflag=pu.on
    self.adcirctstart=0.+self.pg.statim*86400.0 #statim is in days.
    self.adcircdt=0.+self.pg.dt*float(self.couplingdtfactor) #Needed 0+ to prevent the two from being the same object :-/ Careful!!!!
    self.adcircnt=0+self.pg.nt #Needed 0+ to prevent the two from being the same object :-/ Careful!!!!
    self.adcirctprev=self.adcirctstart
    self.adcirctnext=self.adcirctprev
    self.adcirctfinal=(self.pg.statim + self.pg.rnday)*86400.0
    self.adcircntsteps=0+self.pmain.itime_end #Needed 0+ to prevent the two from being the same object :-/ Careful!!!!
    self.adcircfort20pathname=''.join(np.append(np.char.strip(self.ps.inputdir),'/fort.20.new.'+self.couplingtype))
    self.adcircedgestringid=int(argv[argc.value-4])-1
    self.adcircedgestringnnodes=self.pb.nvell[self.adcircedgestringid]
    # We are only accounting for open boundaries and not for closed loops here:
    self.adcircedgestringnodes=self.pb.nbvv[self.adcircedgestringid][1:self.adcircedgestringnnodes+1]
    self.gssharunflag=gsshadefine.ON
    self.gsshatstartjul=self.mvs[0].btime # in Julian date
    self.gsshadt=self.mvs[0].dt # in seconds
    #self.effectivegsshadt=max(60.0, self.mvs[0].dt) # in seconds. This is in case we decide to use niter in mins as ending time
    self.effectivegsshadt=self.mvs[0].dt # in seconds. This is in case we decide to use single_event_end time as ending time
    self.gsshatprev=self.mvs[0].timer # in minutes
    self.gsshatfinal=self.mvs[0].niter # in minutes
    self.gsshasingle_event_end=self.mvs[0].single_event_end # in minutes

################################################################################
if __name__ == '__main__':
    pass

