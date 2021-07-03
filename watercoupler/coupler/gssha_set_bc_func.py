#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
from __future__ import absolute_import, print_function

import gsshapython.sclass.build_options   as gsshaopts
import gsshapython.sclass.define_h        as gsshadefine
import gsshapython.sclass.fnctn_h         as gsshafnctn
from gsshapython.sclass.timeseriesdefs_h import ts_struct

################################################################################
DEBUG_LOCAL = 1

################################################################################
def gssha_set_bc_from_adcirc_depths(ags): # ags is of type adcircgsshatruct.

    from .adcircgsshastruct import SERIESLENGTH, TIME_TOL
    assert(ags.mvs[0].yes_head_bound == 1)
    assert(ags.mvs[0].bound_ts == 1)
    assert(ags.mvs[0].bound_ts_ptr[0].num_vals > 3)
    ts = ags.mvs[0].bound_ts_ptr[0]

    if (ags.pu.debug ==ags.pu.on or gsshaopts._DEBUG == gsshadefine.ON) and DEBUG_LOCAL != 0 and ags.myid == 0:
        print()
        for i in range(ts.num_vals):
            print('Before:(t,v)[',i,'] = (', ts.jul_time[i],',', ts.val[i],')')

    ######################################################
    #SET UP gssha BC from ADCIRC.
    ######################################################
    # Find the value of maximum depth first.
    if (ags.adcircrunflag != ags.pu.off):
        my_max_delta_eta = -1.0e+200
        my_min_delta_eta =  1.0e+200
        count=0.0
        my_avg_delta_eta=0.0
        my_eta_sum=0.0

        for inode in range(ags.adcircedgestringnnodes):
            # -1 needed below since Python is 0 indexed whereas Fortan node numbers are 1-indexed
            node = ags.adcircedgestringnodes[inode]-1
            eta     = ags.pg.eta2[node]
            old_eta = ags.pg.eta1[node]
            my_eta_sum       += eta
            # Gajanan gkc warning : These are only okay to use if the coupling time step is = adcirc time step!
            my_avg_delta_eta += eta - old_eta
            my_max_delta_eta = max(my_max_delta_eta, eta-old_eta)
            my_min_delta_eta = min(my_min_delta_eta, eta-old_eta)
            count += 1.0

        # Note: Hoping whichever depth is closes to GSSHA current depth works better in damping oscillations than dmax alone!
        if (ags.pu.messg==ags.pu.on):
            eta_sum       = ags.pmsg.pymsg_dbl_sum(my_eta_sum      , ags.adcirc_comm_comp)
            avg_delta_eta = ags.pmsg.pymsg_dbl_sum(my_avg_delta_eta, ags.adcirc_comm_comp)
            max_delta_eta = ags.pmsg.pymsg_dbl_max(my_max_delta_eta, ags.adcirc_comm_comp)
            min_delta_eta = ags.pmsg.pymsg_dbl_min(my_min_delta_eta, ags.adcirc_comm_comp)
            count         = ags.pmsg.pymsg_dbl_sum(count           , ags.adcirc_comm_comp)
        else:
            eta_sum       = my_eta_sum
            avg_delta_eta = my_avg_delta_eta
            max_delta_eta = my_max_delta_eta
            min_delta_eta = my_min_delta_eta

        avg_eta = eta_sum/count
        #avg_delta_eta = avg_delta_eta/count # Previous time step
        avg_delta_eta    = avg_eta - ags.adcirc_hprev #Previous stopped ADCIRC time.
        ags.adcirc_hprev = avg_eta
        ags.adcirc_hprev_len = count

        if ags.pu.debug == ags.pu.on or DEBUG_LOCAL != 0:
            print("PE[",ags.myid,"] Edge string(",ags.adcircedgestringid,"): Average eta = ", avg_eta)
            print("PE[",ags.myid,"] Edge string(",ags.adcircedgestringid,"): Maximum delta_eta = ", max_delta_eta)
            print("PE[",ags.myid,"] Edge string(",ags.adcircedgestringid,"): Minimum delta_eta = ", min_delta_eta)
            print("PE[",ags.myid,"] Edge string(",ags.adcircedgestringid,"): Average delta_eta = ", avg_delta_eta)

        if ags.couplingtype == 'gdAdg':
            DT = 0.0
            #while (ags.mvs[0].niter*ags.gsshatimefact+DT < ags.sm[0].submodel[0].t_prev+ags.adcircdt-TIME_TOL):
            #assert(ags.mvs[0].timer*ags.gsshatimefact -TIME_TOL < ags.sm[0].submodel[0].t_prev+ags.adcircdt+TIME_TOL and ags.mvs[0].timer*ags.gsshatimefact + TIME_TOL> ags.sm[0].submodel[0].t_prev)
            while (ags.mvs[0].timer*ags.gsshatimefact + DT < ags.adcirctprev+ags.adcircdt-TIME_TOL):
                DT += ags.effectivegsshadt
        else: # For adg and adgda:
            pass
        #DT = 0.0
        #while (ags.mvs[0].niter*ags.gsshatimefact+DT < ags.sm[0].submodel[0].t_prev-ags.effectivegsshadt+TIME_TOL):
        #    DT += ags.effectivegsshadt
        #if ags.couplingtype == 'gdAdg':
        #    DT += ags.effectivegsshadt
        #print(DT, DT/86400.0)

        # Shift the time series
        for i in range(ts.num_vals-1):
            ts.jul_time[i] = ts.jul_time[i+1]
            ts.val[i]      = ts.val[i+1]
        ts.last_access = ts.last_access-1

        # Add the new value of time.
        ts.jul_time[ts.num_vals-2] = ags.gsshatstartjul+(ags.adcirctprev/86400.0) # Have to convert ADCIRC current time to corresponding next GSSHA Julian time.

        ######################################################################################
        # Gajanan gkc. We need to decide what to use here. Stability is likely going to get
        # affected with this. Also important to consider that GSSHA and ADCIRC may have
        # different values of depths at their interface.

        ## TYPE 1  -  This uses max/min depth.
        ## if abs(ts.val[ts.num_vals-2]-max_depth) < abs(ts.val[ts.num_vals-2]-min_depth):
        #if abs(max_delta_eta) < abs(min_delta_eta):
        #    delta_eta = max_delta_eta
        #else:
        #    delta_eta = min_delta_eta
        #ts.val[ts.num_vals-2] += delta_eta

        # TYPE 2  -  This uses average change in depth.
        ts.val[ts.num_vals-2] += avg_delta_eta

        ######################################################################################


        if ags.couplingtype == 'gdAdg':
            #ts.jul_time[ts.num_vals-2] += max(ags.effectivegsshadt, ags.adcircdt)/86400.0 #Julian
            ts.jul_time[ts.num_vals-2] = ags.mvs[0].btime + DT/86400.0 #Julian
        # For round of errors:
        ts.jul_time[ts.num_vals-1] = ts.jul_time[ts.num_vals-2] + (TIME_TOL/86400.0)
        ts.val[ts.num_vals-1]      = ts.val[ts.num_vals-2]
    else:

        for i in range (ts.num_vals-1):
            ts.jul_time[i] = ts.jul_time[i+1]
            ts.val[i]      = ts.val[i+1]
        ts.jul_time[ts.num_vals-1] += ts.jul_time[ts.num_vals-3]-ts.jul_time[ts.num_vals-4]

    if (ags.pu.debug ==ags.pu.on or gsshaopts._DEBUG == gsshadefine.ON) and DEBUG_LOCAL != 0 and ags.myid == 0:
        print('Current GSSHA julian time =', ags.mvs[0].btime)
        #assert(ags.mvs[0].btime <= ts.jul_time[ts.num_vals-2])
        #assert(ags.mvs[0].btime >= ts.jul_time[0])
        for i in range(ts.num_vals):
            print('After :(t,v)[',i,'] = (', ts.jul_time[i],',', ts.val[i],')')

############################################################################################################
if __name__ == '__main__':
    pass

