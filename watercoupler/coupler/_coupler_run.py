#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
from __future__ import absolute_import, print_function

from ctypes import c_double as ctypes_c_double

################################################################################
import gsshapython.sclass.build_options as gsshaopts
import gsshapython.sclass.types_h       as gsshatypes
import gsshapython.sclass.define_h      as gsshadefine
import gsshapython.sclass.fnctn_h       as gsshafnctn

################################################################################
from .adcirc_init_bc_func import adcirc_init_bc_from_gssha_hydrograph
from .adcirc_set_bc_func  import adcirc_set_bc_from_gssha_hydrograph
from .gssha_init_bc_func  import gssha_init_bc_from_adcirc_depths
from .gssha_set_bc_func   import gssha_set_bc_from_adcirc_depths

################################################################################
DEBUG_LOCAL = 1
###########################################################################
# Gajanan gkc:
# Note: coupler_run_gssha_driving_adcirc and coupler_run_adcirc_driving_gssha
# are very similar functions. The latter was created by copying the former,
# replacing the adcirc_init_bc, adcirc_set_bc functions to gssha_..., exchanging
# the gssha and adcirc running parts in the main while loop, and then only
# correcting the timing information in the nested while condition from
# -ags.adcircdt+TIME_TOL to +ags.gsshadt-TIME_TOL, and
# +ags.adcircdt-TIME_TOL to -ags.gsshadt+TIME_TOL.
# I wonder if this could have been combined into a single function?

#########################################################################functag
def coupler_run_gssha_driving_adcirc(ags):

    from .adcircgsshastruct     import TIME_TOL

    adcirc_init_bc_from_gssha_hydrograph(ags)
    if ags.couplingtype == 'gdAdg':
        gssha_init_bc_from_adcirc_depths(ags)

    # Set final times to zero.
    ags.pmain.itime_end = 0
    ags.mvs[0].niter = 0
    # Run GSSHA only on 1 processsor: PE 0.
    if ags.myid == 0:
        ierr_code = gsshafnctn.main_gssha_run(ags.mvs)
        assert(ierr_code == 0)
        ags.mvs[0].go    = gsshatypes.TRUE
    else:
        # Assumes GSSHA cannot start at negative time!
        ags.mvs[0].go    = gsshatypes.FALSE
    if ags.pu.messg == ags.pu.on:
        if (ags.pu.debug ==ags.pu.on or DEBUG_LOCAL != 0):
            print('PE[',ags.myid,'] Before messg: timer = ', ags.mvs[0].timer)
        ags.mvs[0].timer = ags.pmsg.pymsg_dbl_max(ags.mvs[0].timer, ags.adcirc_comm_comp)
        if (ags.pu.debug ==ags.pu.on or DEBUG_LOCAL != 0):
            print('PE[',ags.myid,'] After messg : timer = ', ags.mvs[0].timer)

    while (ags.adcirctprev<ags.adcirctfinal or ags.mvs[0].timer<ags.gsshatfinal):
        ######################################################
        if (ags.mvs[0].timer < ags.gsshatfinal):
            #while (ags.mvs[0].niter*ags.gsshatimefact < ags.adcirctprev+ags.adcircdt-TIME_TOL):
            #    ags.mvs[0].niter             += int(ags.effectivegsshadt)/60
            #if (ags.adcircrunflag==ags.pu.off): #If ADCIRC is done first, let GSSHA finish off directly.
            #    ags.mvs[0].niter            = ags.gsshatfinal
            ## This one is the important one that determines end time:
            #ags.mvs[0].single_event_end = ags.mvs[0].b_lt_start + ags.mvs[0].niter/1440.0 #float(ags.mvs[0].niter)/1440.0

            # Decided while writing report. Driving model must take at least one time step forward.
            superdt = ags.effectivegsshadt
            #superdt = 0.0
            while (ags.mvs[0].timer*ags.gsshatimefact + superdt < ags.adcirctprev+ags.adcircdt-TIME_TOL):
                superdt                    += ags.effectivegsshadt

            ags.mvs[0].niter               += int(max(1.0, (superdt+TIME_TOL)/60.0))
            # This one is the important one that determines end time:
            ags.mvs[0].single_event_end     = ags.mvs[0].b_lt_start + (ags.mvs[0].timer*ags.gsshatimefact + superdt)/86400.0 #Julian

            if (ags.adcircrunflag==ags.pu.off): #If ADCIRC is done first, let GSSHA finish off directly.
                ags.mvs[0].niter            = ags.gsshatfinal
                ags.mvs[0].single_event_end = ags.mvs[0].b_lt_start + ags.mvs[0].niter/1440.0 #gsshatfinal was original niter in mins

            if gsshaopts._DEBUG == gsshadefine.ON and DEBUG_LOCAL != 0 and ags.myid == 0:
                print("\n*******************************************\nRunning GSSHA:")
                print("dt             =", ags.mvs[0].dt)
                print("timer          =", ags.mvs[0].timer)
                print("niter          =", ags.mvs[0].niter)
                print("superdt        =", superdt)
                print("end time       =", ags.mvs[0].timer*ags.gsshatimefact + superdt)
            elif ags.myid==0:
                print("\n*******************************************\nRunning GSSHA:")

            # Run GSSHA only on 1 processsor: PE 0.
            if ags.myid == 0:
                ierr_code = gsshafnctn.main_gssha_run(ags.mvs)
                assert(ierr_code == 0)
                # Needed to force gssha to run for next time step:
                ags.mvs[0].go    = gsshatypes.TRUE
            else:
                # Note: We are keeping gssharunflag as ON, but mvs[0].go as FALSE!!
                # This matters in adcirc_set_bc functions!
                ags.mvs[0].go    = gsshatypes.FALSE
            if ags.pu.messg == ags.pu.on:
                if (ags.pu.debug ==ags.pu.on or DEBUG_LOCAL != 0):
                    print('PE[',ags.myid,'] Before messg: timer = ', ags.mvs[0].timer)
                ags.mvs[0].timer = ags.pmsg.pymsg_dbl_max(ctypes_c_double(ags.mvs[0].timer), ags.adcirc_comm_comp)
                if (ags.pu.debug ==ags.pu.on or DEBUG_LOCAL != 0):
                    print('PE[',ags.myid,'] After messg : timer = ', ags.mvs[0].timer)

        else:
            ags.gssharunflag = gsshadefine.OFF
            ags.mvs[0].go    = gsshatypes.FALSE

        ######################################################
        # Set ADCIRC Boundary conditions from GSSHA
        adcirc_set_bc_from_gssha_hydrograph(ags)

        ######################################################
        if (ags.adcirctprev < ags.adcirctfinal):
            ntsteps = 0
            while (ags.adcirctnext < ags.mvs[0].timer*ags.gsshatimefact-ags.adcircdt+TIME_TOL):
                ntsteps += ags.couplingdtfactor
                ags.adcirctnext += ags.adcircdt
            if (ags.gssharunflag == gsshadefine.OFF):
                ntsteps = (ags.adcircntsteps-ags.pmain.itime_bgn+1)
                ags.adcirctnext = ags.adcirctfinal

            if ags.pu.debug == ags.pu.on and DEBUG_LOCAL != 0 and ags.myid == 0:
                print("\n****************************************\nRunning ADCIRC:")
                print("dt             =", ags.adcircdt)
                print("t_prev         =", ags.adcirctprev)
                print("t_final        =", ags.adcirctnext)
                print("ntsteps        =", ntsteps)
            elif ags.myid==0:
                print("\n****************************************\nRunning ADCIRC:")

            # Run ADCIRC
            ags.pmain.pyadcirc_run(ntsteps)
            ags.adcirctprev = (ags.pmain.itime_bgn-1)*ags.pg.dtdp + ags.pg.statim*86400.0

        else:
            ags.adcircrunflag=ags.pu.off

        ######################################################
        ## Set GSSHA Boundary conditions from ADCIRC
        if ags.couplingtype == 'gdAdg':
            gssha_set_bc_from_adcirc_depths(ags)

#########################################################################functag
def coupler_run_adcirc_driving_gssha(ags):

    from .adcircgsshastruct     import TIME_TOL

    gssha_init_bc_from_adcirc_depths(ags)
    if ags.couplingtype == 'AdgdA':
       adcirc_init_bc_from_gssha_hydrograph(ags)

    # Set final times to zero.
    ags.pmain.itime_end = 0
    ags.mvs[0].niter = 0
    # Run GSSHA only on 1 processsor: PE 0.
    if ags.myid == 0:
        ierr_code = gsshafnctn.main_gssha_run(ags.mvs)
        assert(ierr_code == 0)
        ags.mvs[0].go    = gsshatypes.TRUE
    else:
        # Assumes GSSHA cannot start at negative time!
        ags.mvs[0].go    = gsshatypes.FALSE
    if ags.pu.messg == ags.pu.on:
        if (ags.pu.debug ==ags.pu.on or DEBUG_LOCAL != 0):
            print('PE[',ags.myid,'] Before messg: timer = ', ags.mvs[0].timer)
        ags.mvs[0].timer = ags.pmsg.pymsg_dbl_max(ags.mvs[0].timer, ags.adcirc_comm_comp)
        if (ags.pu.debug ==ags.pu.on or DEBUG_LOCAL != 0):
            print('PE[',ags.myid,'] After messg : timer = ', ags.mvs[0].timer)

    while (ags.adcirctprev<ags.adcirctfinal or ags.mvs[0].timer<ags.gsshatfinal):
        ######################################################
        if (ags.adcirctprev < ags.adcirctfinal):
            ntsteps = 0
            while (ags.adcirctnext < ags.mvs[0].timer*ags.gsshatimefact+ags.effectivegsshadt-TIME_TOL):
            #while (ags.adcirctnext < ags.mvs[0].timer*ags.gsshatimefact+ags.adcircdt-TIME_TOL):
                ntsteps += ags.couplingdtfactor
                ags.adcirctnext += ags.adcircdt
            if (ags.gssharunflag == gsshadefine.OFF):
                ntsteps = (ags.adcircntsteps-ags.pmain.itime_bgn+1)
                ags.adcirctnext = ags.adcirctfinal

            if ags.pu.debug == ags.pu.on and DEBUG_LOCAL != 0 and ags.myid == 0:
                print("\n****************************************\nRunning ADCIRC:")
                print("dt             =", ags.adcircdt)
                print("t_prev         =", ags.adcirctprev)
                print("t_final        =", ags.adcirctnext)
                print("ntsteps        =", ntsteps)
            elif ags.myid==0:
                print("\n****************************************\nRunning ADCIRC:")

            # Run ADCIRC
            ags.pmain.pyadcirc_run(ntsteps)
            ags.adcirctprev = (ags.pmain.itime_bgn-1)*ags.pg.dtdp + ags.pg.statim*86400.0

        else:
            ags.adcircrunflag=ags.pu.off

        ######################################################
        ## Set GSSHA Boundary conditions from ADCIRC
        gssha_set_bc_from_adcirc_depths(ags)

        ######################################################
        if (ags.mvs[0].timer < ags.gsshatfinal):
            #while (ags.mvs[0].niter*ags.gsshatimefact < ags.adcirctprev-ags.adcircdt+TIME_TOL):
            #    ags.mvs[0].niter             += int(ags.effectivegsshadt)/60
            #if (ags.adcircrunflag==ags.pu.off): #If ADCIRC is done first, let GSSHA finish off directly.
            #    ags.mvs[0].niter            = ags.gsshatfinal
            ## This one is the important one that determines end time:
            #ags.mvs[0].single_event_end = ags.mvs[0].b_lt_start + ags.mvs[0].niter/1440.0 #float(ags.mvs[0].niter)/1440.0

            # Decided while writing report. Driving model must take at least one time step forward.
            superdt = ags.effectivegsshadt
            #superdt = 0.0
            while (ags.mvs[0].timer*ags.gsshatimefact + superdt < ags.adcirctprev-ags.effectivegsshadt+TIME_TOL):
                superdt                    += ags.effectivegsshadt

            ags.mvs[0].niter               += int(max(1.0, (superdt+TIME_TOL)/60.0))
            # This one is the important one that determines end time:
            ags.mvs[0].single_event_end     = ags.mvs[0].b_lt_start + (ags.mvs[0].timer*ags.gsshatimefact + superdt)/86400.0 #Julian

            if (ags.adcircrunflag==ags.pu.off): #If ADCIRC is done first, let GSSHA finish off directly.
                ags.mvs[0].niter            = ags.gsshatfinal
                ags.mvs[0].single_event_end = ags.mvs[0].b_lt_start + ags.mvs[0].niter/1440.0 #gsshatfinal was original niter in mins

            if gsshaopts._DEBUG == gsshadefine.ON and DEBUG_LOCAL != 0 and ags.myid == 0:
                print("\n*******************************************\nRunning GSSHA:")
                print("dt             =", ags.mvs[0].dt)
                print("timer          =", ags.mvs[0].timer)
                print("niter          =", ags.mvs[0].niter)
                print("superdt        =", superdt)
                print("end time       =", ags.mvs[0].timer*ags.gsshatimefact + superdt)
            elif ags.myid==0:
                print("\n*******************************************\nRunning GSSHA:")

            # Run GSSHA only on 1 processsor: PE 0.
            if ags.myid == 0:
                ierr_code = gsshafnctn.main_gssha_run(ags.mvs)
                assert(ierr_code == 0)
                # Needed to force gssha to run for next time step:
                ags.mvs[0].go    = gsshatypes.TRUE
            else:
                # Note: We are keeping gssharunflag as ON, but mvs[0].go as FALSE!!
                # This matters in adcirc_set_bc functions!
                ags.mvs[0].go    = gsshatypes.FALSE
            if ags.pu.messg == ags.pu.on:
                if (ags.pu.debug ==ags.pu.on or DEBUG_LOCAL != 0):
                    print('PE[',ags.myid,'] Before messg: timer = ', ags.mvs[0].timer)
                ags.mvs[0].timer = ags.pmsg.pymsg_dbl_max(ctypes_c_double(ags.mvs[0].timer), ags.adcirc_comm_comp)
                if (ags.pu.debug ==ags.pu.on or DEBUG_LOCAL != 0):
                    print('PE[',ags.myid,'] After messg : timer = ', ags.mvs[0].timer)

        else:
            ags.gssharunflag = gsshadefine.OFF
            ags.mvs[0].go    = gsshatypes.FALSE

        ######################################################
        # Set ADCIRC Boundary conditions from GSSHA
        if ags.couplingtype == 'AdgdA':
            adcirc_set_bc_from_gssha_hydrograph(ags)


#########################################################################functag
def adcircgssha_coupler_run(self):

    if self.couplingtype == 'gdA':
        run_string = 'Running GSSHA driving ADCIRC, One-way coupling'
        run_func = coupler_run_gssha_driving_adcirc

    elif self.couplingtype == 'Adg':
        run_string = 'Running ADCIRC driving GSSHA, One-way coupling'
        run_func = coupler_run_adcirc_driving_gssha

    elif self.couplingtype == 'gdAdg':
        run_string = 'Running GSSHA driving ADCIRC driving GSSHA, Two-way coupling'
        run_func = coupler_run_gssha_driving_adcirc

    elif self.couplingtype == 'AdgdA':
        run_string = 'Running ADCIRC driving GSSHA driving ADCIRC, Two-way coupling'
        run_func = coupler_run_adcirc_driving_gssha

    else:
        print('Unkown coupling type supplied by user:', self.couplingtype, '\nExiting.')
        return

    print("\n\n***************************************************************")
    print(    "***************************************************************")
    print(    run_string)
    print(    "***************************************************************")
    print(    "***************************************************************")

    run_func(self)

    print("\n\n***************************************************************")
    print(    "***************************************************************")
    print(    "Finished", run_string)
    print(    "***************************************************************")
    print(    "***************************************************************")


#########################################################################functag
if __name__ == '__main__':
    pass

