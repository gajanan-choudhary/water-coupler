#!/usr/bin/env python
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#

################################################################################
import gsshapython.sclass.build_options as gsshaopts
import gsshapython.sclass.define_h      as gsshadefine
import gsshapython.sclass.fnctn_h       as gsshafnctn

################################################################################
DEBUG_LOCAL = 1

################################################################################
def adcircgssha_coupler_finalize(self):

    if gsshaopts._DEBUG==gsshadefine.ON and DEBUG_LOCAL!=0 and self.myid==0:
        print "Finalizing GSSHA"
    ierr_code = gsshafnctn.main_gssha_finalize(self.mvs)
    if self.myid==0:
        print "*********************** GSSHA Finalized ***********************"
        print "***************************************************************"

    if self.pu.debug==self.pu.on and DEBUG_LOCAL!=0 and self.myid==0:
        print '\n\nFinalizing ADCIRC\n'
    ierr_code = self.pmain.pyadcirc_finalize()
    if self.myid==0:
        print "********************** ADCIRC Finalized ***********************"
        print "***************************************************************"


################################################################################

if __name__ == '__main__':
    pass
