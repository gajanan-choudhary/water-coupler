#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
from __future__ import absolute_import, print_function

import gsshapython.sclass.build_options   as gsshaopts
import gsshapython.sclass.define_h        as gsshadefine
import gsshapython.sclass.fnctn_h         as gsshafnctn

################################################################################
DEBUG_LOCAL = 1

################################################################################
def gssha_init_bc_from_adcirc_depths(ags): # ags is of type adcircgsshatruct.
    from .adcircgsshastruct import SERIESLENGTH
    assert(ags.mvs[0].yes_head_bound == 1)
    assert(ags.mvs[0].bound_ts == 1)
    assert(ags.mvs[0].bound_ts_ptr)
    assert(ags.mvs[0].bound_ts_ptr[0].num_vals >= SERIESLENGTH)

    ######################################################
    #SET UP gssha BC from ADCIRC.
    ######################################################
    # Find the value of maximum depth first.
    eta=0.0
    my_eta_sum =  0.0
    my_max_eta = -1.0e+200
    my_min_eta =  1.0e+200
    count=0.0

    for inode in range(ags.adcircedgestringnnodes):
        # -1 needed below since Python is 0 indexed whereas Fortan node numbers are 1-indexed
        node = ags.adcircedgestringnodes[inode]-1
        eta = ags.pg.eta2[node]
        my_eta_sum += eta
        my_max_eta = max(my_max_eta, eta)
        my_min_eta = min(my_min_eta, eta)
        count += 1.0

    # Note: Hoping whichever depth is closes to GSSHA current depth works better in damping oscillations than dmax alone!
    if (ags.pu.messg==ags.pu.on):
        eta_sum = ags.pmsg.pymsg_dbl_sum(my_eta_sum, ags.adcirc_comm_comp)
        max_eta = ags.pmsg.pymsg_dbl_max(my_max_eta, ags.adcirc_comm_comp)
        min_eta = ags.pmsg.pymsg_dbl_min(my_min_eta, ags.adcirc_comm_comp)
        count   = ags.pmsg.pymsg_dbl_sum(count     , ags.adcirc_comm_comp)
    else:
        eta_sum = my_eta_sum
        max_eta = my_max_eta
        min_eta = my_min_eta
    avg_eta = eta_sum/count
    ags.adcirc_hprev = avg_eta # Going to be taking the average.
    ags.adcirc_hprev_len = count # Going to be taking the average.
    print("PE[",ags.myid,"] Edge string(",ags.adcircedgestringid,"): Starting Average eta2 = ", ags.adcirc_hprev, "count = ", ags.adcirc_hprev_len)


    ######################################################
    ts = ags.mvs[0].bound_ts_ptr[0]
    if (ags.pu.debug == ags.pu.on or gsshaopts._DEBUG == gsshadefine.ON) and DEBUG_LOCAL != 0 and ags.myid == 0:
        print('\nSetting up Boundary time series for GSSHA.')
        for i in range(ts.num_vals):
            print('Before:(t,v)[',i,'] = (', ts.jul_time[i],',', ts.val[i],')')

    superdt = 0.0
    while (superdt < ags.adcirctstart + ags.adcircdt):
        # Should be the commented one ideally, but GSSHA starts with a minimum 1 minute run, causing issues. Had to replace with max(...)
        superdt += ags.effectivegsshadt
        #superdt += max(60.0, ags.effectivegsshadt)
    superdt = superdt/86400.0

    for i in range(ts.num_vals):
        ts.jul_time[i] = ags.mvs[0].btime - (ts.num_vals-2-i) * superdt # max(ags.effectivegsshadt, ags.adcircdt)/86400.0
        ts.val[i]      = ags.mvs[0].boundary_depth
        if ags.couplingtype == 'gdAdg':
            ts.jul_time[i] += superdt #max(ags.effectivegsshadt, ags.adcircdt)/86400.0
    ts.jul_time[ts.num_vals-1] = ts.jul_time[ts.num_vals-2] + ags.effectivegsshadt/86400.0 # max(ags.effectivegsshadt, ags.adcircdt)/86400.0

    if (ags.pu.debug == ags.pu.on or gsshaopts._DEBUG == gsshadefine.ON) and DEBUG_LOCAL != 0 and ags.myid == 0:
        for i in range(ts.num_vals):
            print('After :(t,v)[',i,'] = (', ts.jul_time[i],',', ts.val[i],')')
    #exit()

################################################################################
if __name__ == '__main__':
    pass

