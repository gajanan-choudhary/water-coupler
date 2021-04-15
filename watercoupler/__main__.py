#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
"""
Main function of watercoupler that gets invoked on the command line.
"""

from __future__ import absolute_import

if (__package__ == "watercoupler"):
    from . import watercoupler_path as _watercoupler_path
    from .main import main
elif (__name__ == "__main__"):
    import watercoupler_path as _watercoupler_path
    from watercoupler.main import main
else:
    from . import watercoupler_path as _watercoupler_path
    from .main import main

#------------------------------------------------------------------------------#
if __name__ == '__main__':
    main()

