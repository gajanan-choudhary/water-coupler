#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
from __future__ import absolute_import, print_function
import numpy as np

################################################################################
DEBUG_LOCAL = 1

################################################################################
def adcirc_init_bc_from_gssha_hydrograph(ags): # ags is of type adcircgsshatruct.

    from .adcircgsshastruct import SERIESLENGTH, TIME_TOL

    ######################################################
    #SET UP ADCIRC BC series and edgestring.
    ######################################################
    assert(ags.pb.ibtype[ags.adcircedgestringid] == 22)

    ######################################################
    # Store the length of the coupled ADCIRC edge string
    # Valid only for open boundary and not a closed one!
    for inode in range(1,ags.adcircedgestringnnodes):
        # -1 needed below since Python is 0 indexed whereas Fortan node numbers are 1-indexed
        n1 = ags.adcircedgestringnodes[inode-1]-1
        n2 = ags.adcircedgestringnodes[inode  ]-1
        x1 = ags.pm.x[n1]
        y1 = ags.pm.y[n1]
        x2 = ags.pm.x[n2]
        y2 = ags.pm.y[n2]
        delx = x2-x1
        dely = y2-y1
        ags.adcircedgestringlen += np.sqrt(delx*delx+dely*dely)
        if ags.pu.debug == ags.pu.on and DEBUG_LOCAL != 0:
            print("Nodes ",n1,"(",x1,",",y1,"),",n2,"(",x2,",",y2,")")
    if ags.pu.messg==ags.pu.on:
        ags.adcircedgestringlen = ags.pmsg.pymsg_dbl_sum(ags.adcircedgestringlen, ags.adcirc_comm_comp)
    if ags.pu.debug == ags.pu.on and DEBUG_LOCAL != 0:
        print("Edge string(",ags.adcircedgestringid+1,"): Length = ", ags.adcircedgestringlen)

    ######################################################
    # Find series to modify during coupling.
    assert (SERIESLENGTH>=2)

    if ags.pu.debug == ags.pu.on and DEBUG_LOCAL != 0 and ags.myid==0:
        nbvStartIndex=sum(ags.pb.nvell[:ags.adcircedgestringid])
        print("Original: Flux time increment FTIMINC =", ags.pg.ftiminc,\
                "\nOriginal: Flux times:\nQTIME1 =", ags.pg.qtime1, \
                "\nQTIME2 =", ags.pg.qtime2, \
                "\nOriginal: Flux values:\nQNIN1  =\n",  ags.pg.qnin1[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes], \
                "\nQNIN2  =\n",  ags.pg.qnin2[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes])

    ##################################################
    # Replace the flux time increment value.
    if ags.adcirctstart > 0.0: # GSSHA starting time is before ADCIRC starting time; GSSHA always starts at 0.0, hopefully!
        superdt = ags.adcircdt
    else:
        superdt = ags.adcirctstart
        while (superdt < ags.effectivegsshadt - TIME_TOL):
            superdt += ags.adcircdt #max(ags.effectivegsshadt, ags.adcircdt)
        superdt -= ags.adcirctstart

    assert(ags.adcircdt>ags.gsshadt) #If this is true, then superdt = either adcirctstart or adcircdt.
    ags.pg.ftiminc = superdt

    ######################################################
    # Close the original fort.20, write a new one with a different name, and reopen it for reading
    errorio = ags.pu.pycloseopenedfileforread(20)
    assert(errorio==0)

    # Replace the fort.20 file.
    with open(ags.adcircfort20pathname, 'w') as fort20file:
        [fort20file.write('0.0\n') for i in range(ags.adcircedgestringnnodes*SERIESLENGTH)]

    errorio = ags.pg.pyopenfileforread(20,ags.adcircfort20pathname)
    assert(errorio==0)

    ##################################################
    # Replace the flux times and values.
    nbvStartIndex=sum(ags.pb.nvell[:ags.adcircedgestringid])
    ags.pg.qnin2[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes+1] = 0.0
    with open(ags.adcircfort20pathname, 'w') as fort20file:
        #Set series value to zero
        #ags.adcircseries[0].entry[i].value[0] = 0.0
        for dumm in range(SERIESLENGTH):
            for i in range(ags.pb.nvel):
                if ags.pb.lbcodei[i] in [2, 12, 22]:
                    [fort20file.write('{0:10f}\n'.format(ags.pg.qnin2[i]))]
                if ags.pb.lbcodei[i] == 32:
                    [fort20file.write('{0:10f}  {1:10f}\n'.format(ags.pg.qnin2[i],ags.pg.enin2[i]))]
        #Set starting time to <whatever>
        #ags.adcircseries[0].entry[i].time = ags.adcirctstart + i*superdt
        #if ags.couplingtype == 'AdgdA':
        #    ags.adcircseries[0].entry[i].time += superdt # If 2-way AdgdA, then time series has to be shifted ahead since ADCIRC goes first.
    ags.pg.qtime1 = ags.adcirctstart-superdt
    ags.pg.qtime2 = ags.pg.qtime1+ags.pg.ftiminc
    if ags.couplingtype == 'AdgdA':
        ags.pg.qtime1 += superdt
        ags.pg.qtime2 += superdt
    #for i in range(ags.adcircseries[0].size):
    #    ags.adcircseries[0].entry[i].value[0] = 0.0
    #    ags.adcircseries[0].entry[i].time = ags.adcirctstart - (ags.adcircseries[0].size-2-i)*superdt
    #    if ags.couplingtype == 'AdgdA':
    #        ags.adcircseries[0].entry[i].time += superdt # If 2-way AdgdA, then time series has to be shifted ahead since ADCIRC goes first.

    # Play around with this if you are having problem with ADCIRC BC Series Starting time.
    if ags.adcirctstart > 0:  # If ADCIRC starting time is later than GSSHA. GSSHA always starts at 0.
        #for i in range(SERIESLENGTH-2):
        #    ags.adcircseries[0].entry[i].time -= ags.adcirctstart
        if ags.couplingtype != 'AdgdA':
            #ags.adcircseries[0].entry[ags.adcircseries[0].size-2].time -= ags.adcirctstart
            ags.pg.qtime1 -= ags.adcirctstart
            ags.pg.ftiminc += ags.adcirctstart ## Gajanan gkc warning caution: Newly added in 03/2020
                                               ## Ensure this gets replaced in set_bc function.

    if ags.pu.debug == ags.pu.on and DEBUG_LOCAL != 0:
        print("Replaced: Flux time increment FTIMINC =", ags.pg.ftiminc,\
                "\nReplaced: Flux times:\nQTIME1 =", ags.pg.qtime1, \
                "\nQTIME2 =", ags.pg.qtime2, \
                "\nReplaced: Flux values:\nQNIN1  =\n",  ags.pg.qnin1[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes], \
                "\nQNIN2  =\n",  ags.pg.qnin2[nbvStartIndex : nbvStartIndex+ags.adcircedgestringnnodes])

################################################################################
if __name__ == '__main__':
    pass

