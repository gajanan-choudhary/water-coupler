#!/usr/bin/env python
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
"""
Main function of watercoupler that gets invoked on the command line.
"""

if __name__ == "__main__":
    import watercoupler_path
    from main import main
else:
    from . import watercoupler_path
    from .main import main

################################################################################
if __name__ == '__main__':
    main()

