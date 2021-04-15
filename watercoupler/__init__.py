#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# watercoupler - Software for coupling hydrodynamic and hydrologic software
# LICENSE: BSD 3-Clause "New" or "Revised"
#------------------------------------------------------------------------------#
"""
The main watercoupler module.

Contains the main watercoupler function imported as "main".
"""

from __future__ import absolute_import, print_function

if __name__ == '__main__':
    import watercoupler_path as _watercoupler_path
else:
    from . import watercoupler_path as _watercoupler_path

from watercoupler.main import main

__all__ = ['main', ]

#------------------------------------------------------------------------------#
if (__name__ == '__main__'):
    pass

