#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
from __future__ import absolute_import, print_function

import gsshapython.sclass.build_options as gsshaopts
import gsshapython.sclass.define_h      as gsshadefine

################################################################################
DEBUG_LOCAL = 1
################################################################################
def adcirc_set_bc_from_gssha_hydrograph(ags): # ags is of type adcircgsshatruct.

    from .adcircgsshastruct import SERIESLENGTH, TIME_TOL

    ########## Set ADCIRC Boundary Conditions ###########
    # Note: ags.adcircseries already points to the head of series in ADCIRC that needs to be modified.
    nbvStartIndex=sum(ags.pb.nvell[:ags.adcircedgestringid])
    if ags.pu.debug == ags.pu.on and DEBUG_LOCAL != 0 and ags.myid==0:
        print("\nOriginal: Flux time increment FTIMINC =", ags.pg.ftiminc,\
                "\nOriginal: Flux times:\nQTIME1 =", ags.pg.qtime1, \
                "\nQTIME2 =", ags.pg.qtime2, \
                "\nOriginal: Flux values:\nQNIN1  =\n",  ags.pg.qnin1[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes], \
                "\nQNIN2  =\n",  ags.pg.qnin2[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes])

    if ags.pu.messg == ags.pu.on:
        if ags.myid != 0:
            messgvout  = -1.0E+200
        else:
            messgvout  = ags.mvs[0].vout
        if (ags.pu.debug ==ags.pu.on or gsshaopts._DEBUG == gsshadefine.ON) or DEBUG_LOCAL != 0:
            print('PE[',ags.myid,'] Before messg: vout = ', ags.mvs[0].vout)
        ags.mvs[0].vout  = ags.pmsg.pymsg_dbl_max(messgvout, ags.adcirc_comm_comp)
        if (ags.pu.debug ==ags.pu.on or gsshaopts._DEBUG == gsshadefine.ON) or DEBUG_LOCAL != 0:
            print('PE[',ags.myid,'] After messg : vout = ', ags.mvs[0].vout)

    ######################################################
    # Close the original fort.20
    errorio = ags.pu.pycloseopenedfileforread(20)
    assert(errorio==0)

    if (ags.gssharunflag != gsshadefine.OFF):

        # Inflow volume in the current gssha time step:
        # V=(t2-t1)(q1+q2)/2; So to conserve mass entering in ADCIRC in interval t2-t1, q2 = 2*V/(t2-t1) - q1  in cu.m/s
        # Therefore, in (cu.m/s)/m, ADCIRC series value be val2 = 2*V/(t2-t1)/edgestringleng - val1; since val_i=q_i/edgestringlen
        DV = (ags.mvs[0].vout-ags.gsshavoutprev)
        if ags.couplingtype == 'AdgdA':
            DT = 0.0
            ags.adcirctprev=ags.pu.pyfindelapsedtime(ags.pmain.itime_end) #Last time at which ADCIRC was paused & solution known
            while (ags.adcirctprev + DT < ags.mvs[0].timer*ags.gsshatimefact+ags.effectivegsshadt-TIME_TOL):
                DT += ags.adcircdt
        else: # For gda and gdadg:
            DT = (ags.mvs[0].timer-ags.gsshavoutprev_t)*ags.gsshatimefact + 1.0E-20

        if (ags.pu.debug ==ags.pu.on or gsshaopts._DEBUG == gsshadefine.ON) and DEBUG_LOCAL != 0 and ags.myid == 0:
            # This is valid only for PE 0 which is running GSSHA. Not on other PEs!
            outlet_area  = ags.mvs[0].area[      ags.mvs[0].nx[ags.mvs[0].nlinks]][ags.mvs[0].nlinks]
            outlet_depth = ags.mvs[0].chan_depth[ags.mvs[0].nx[ags.mvs[0].nlinks]][ags.mvs[0].nlinks]
            print("outlet area       =", outlet_area, "m2")
            print("outlet chan_depth =", outlet_depth, "m")
            print("qout              =", ags.mvs[0].qout, "m3/s")
            print("voutprev          =", ags.gsshavoutprev, "m3")
            print("vout              =", ags.mvs[0].vout, "m3")
            print("DV                =", DV, "m3")
            print("DT                =", DT, "s")
            print("GSSHA qout/area   =", ags.mvs[0].qout / outlet_area,"m/s")
            print("Avg. GSSHA speed  ~", DV / DT / outlet_area, "m/s")
            print("Avg. ADCIRC speed ~", DV / DT, "(m3/s) / ADCIRC area (needs more work!)")

        if DV < 0.0:
            print("Warning: Outflow from ADCIRC model forced by GSSHA! This can cause instabilities in the model!")

        # Move current to previous: Current is at [2], previous is at [1]
        # Shift values backward
        ags.pg.qtime1 = ags.pg.qtime2
        for i in range(len(ags.pg.qnin1)):
            ags.pg.qnin1[i] = ags.pg.qnin2[i]

        # Set ADCIRC series value for gssha time t2
        ags.pg.qtime2 = ags.mvs[0].timer*ags.gsshatimefact # This is GSSHA time set in ADCIRC series.
        if ags.couplingtype == 'AdgdA':
            ags.pg.qtime2 = ags.adcirctprev+DT #ags.adcircdt # If 2-way AdgdA, then time series has to be shifted ahead since ADCIRC goes first.

        # ADCIRC Series value
        #DT_calculated = ags.adcircseries[0].entry[SERIESLENGTH-2].time - ags.adcircseries[0].entry[SERIESLENGTH-3].time
        #print("DT_calculated     =", DT_calculated, "s")
        #DT_calculated affects how the mass is distributed. If we want to dump all the mass from GSSHA into ADCIRC's next time step
        #no matter how large it may be, we should use DT_calculated. For now, I'm skipping DT_calculated.
        oldseriesvalue = ags.pg.qnin2[nbvStartIndex]
        #seriesvalue = (2*DV/DT/ags.adcircedgestringlen * ags.gsshahydrofact - oldseriesvalue)
        seriesvalue =  ags.mvs[0].qout/ags.adcircedgestringlen
        ags.pg.qnin2[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes] = seriesvalue
        with open(ags.adcircfort20pathname, 'w') as fort20file:
            #print("QNIN values start at", nbvStartIndex)
            for i in range(ags.pb.nvel):
                if ags.pb.lbcodei[i] in [2, 12, 22]:
                    [fort20file.write('{0:10f}\n'.format(ags.pg.qnin2[i]))]
                if ags.pb.lbcodei[i] == 32:
                    [fort20file.write('{0:10f}  {1:10f}\n'.format(ags.pg.qnin2[i],ags.pg.enin2[i]))]
            # Now set the last value same as the current value, but not the time!
            # TO IMPLEMENT THIS PART, JUST WRITE THE SERIES TWICE IN fort.22 replacement!
            #ags.adcircseries[0].entry[SERIESLENGTH-1].time     = ags.adcircseries[0].entry[SERIESLENGTH-2].time + TIME_TOL
            #ags.adcircseries[0].entry[SERIESLENGTH-1].value[0] = ags.adcircseries[0].entry[SERIESLENGTH-2].value[0]
            for i in range(ags.pb.nvel):
                if ags.pb.lbcodei[i] in [2, 12, 22]:
                    [fort20file.write('{0:10f}\n'.format(ags.pg.qnin2[i]))]
                if ags.pb.lbcodei[i] == 32:
                    [fort20file.write('{0:10f}  {1:10f}\n'.format(ags.pg.qnin2[i],ags.pg.enin2[i]))]

        # Calculate slope
        ags.adcircseriesslope = \
                (seriesvalue - oldseriesvalue) / \
                (ags.pg.qtime2 - ags.pg.qtime1)#+1.0E-14)

        # Calculate 'area', i.e., volume/unit width that has flown in at this time step.
        ags.adcircseriesarea  = 0.5 * \
                (seriesvalue + oldseriesvalue) * \
                (ags.pg.qtime2 - ags.pg.qtime1)

        #Store volume for the next time step.
        ags.gsshavoutprev   = ags.mvs[0].vout
        ags.gsshavoutprev_t = ags.mvs[0].timer

    else:
        # Shift values backward
        ags.pg.qtime1 = ags.pg.qtime2
        for i in range(ags.pb.nvel):
            ags.pg.qnin1[i] = ags.pg.qnin2[i]
        # Replace the fort.20 file.
        with open(ags.adcircfort20pathname, 'w') as fort20file:
            [fort20file.write('0.0\n') for i in range(ags.adcircedgestringnnodes*SERIESLENGTH)]
        # Reset the flux time increment
        # Gajanan gkc warning: Note that this will cause a problem if there are multiple non-zero-flux boundaries!!!
        ags.pg.ftiminc = abs(ags.adcirctfinal)*10.0

    ######################################################
    # Reopen the fort.20 replacement file
    errorio = ags.pg.pyopenfileforread(20,ags.adcircfort20pathname)
    assert(errorio==0)

    if ags.pu.debug == ags.pu.on and DEBUG_LOCAL != 0:
        print("Replaced: Flux time increment FTIMINC =", ags.pg.ftiminc,\
                "\nReplaced: Flux times:\nQTIME1 =", ags.pg.qtime1, \
                "\nQTIME2 =", ags.pg.qtime2, \
                "\nReplaced: Flux values:\nQNIN1  =\n",  ags.pg.qnin1[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes], \
                "\nQNIN2  =\n",  ags.pg.qnin2[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes])
        print('Area   contained  =', ags.adcircseriesarea)
        print('Volume contained  =', ags.adcircseriesarea*ags.adcircedgestringlen)


############################################################################################################
if __name__ == '__main__':
    pass
