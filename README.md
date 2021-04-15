# Water Coupler - Python coupler for ADCIRC and GSSHA

Water Coupler is a Python software for coupling ADvanced CIRCulation
([ADCIRC](http://adcirc.org/)) and Gridded Surface Subsurface Hydrologic
Analysis ([GSSHA](https://www.gsshawiki.com/)). Coupling with other software may
be added in the future. The code is intended to run in serial as well as
parallel.


## Getting Started

### Dependencies

* Python 2x or 3x (tested on 2.7 and 3.6),
* [NumPy](https://numpy.org/)
* ADCIRC shared libraries : `libadcpy.so`/`libpadcpy.so` and `pyadcirc.so`
* ADCIRC python interface : `pyADCIRC`
* GSSHA shared library    : `libgssha.so`
* GSSHA python interface  : `gsshapython`

### Installing

After (pip-) installing the prerequisites, `pyADCIRC` and `gsshapython`,
pip-install `watercoupler` as well, as follows:
```bash
cd <path_to_water-coupler_repo_root>
python3 -m pip install .
```

### Running tests

Currently, no automated tests have been enabled for `watercoupler`. However, a
repository of testcases is being developed; see
[water-coupler-tests](https://github.com/gajanan-choudhary/water-coupler-tests).


## Using the project

Suppose you want to run a coupled ADCIRC-GSSHA simulation, with ADCIRC files
named `fort.*` and GSSHA files named `Stream*`, including the project file
`Stream.prj`. Copy the ADCIRC and GSSHA input files in a single directory. Run
`watercoupler` as a python module with the following command line arguments:
 - Argument 1: Boundary string ID of the ADCIRC model that is being coupled,
 - Argument 2: One of the following coupling type identifiers,
   * `Adg`   - One-way coupling with ADCIRC driving GSSHA,
   * `gdA`   - One-way coupling with GSSHA driving ADCIRC,
   * `AdgdA` - Two-way coupling with ADCIRC "driving" (staying ahead of) GSSHA,
   * `gdAdg` - Two-way coupling with GSSHA "driving" (staying ahead of) ADCIRC,
 - Argument 3: Name of GSSHA Project file, e.g., `Stream.prj`, and
 - Argument 4: Name of ADCIRC Project file, e.g., `fort` (currently ignored).

For instance, the Linux/Unix workflow goes as follows.
```bash
mkdir sample-sim
cd sample-sim
cp -r <path_to_ADCIRC_input_files>/* .
cp -r <path_to_GSSHA_input_files>/* .

python3 -m watercoupler \
    <ADCIRC model coupled boundary> \
    <Coupling type identifier> \
    <GSSHA project file name> \
    <ADCIRC project file name without extension>
```

For parallel runs when pyADCIRC has been compiled in parallel, you may run
```bash
mpirun  -np <num_procs>  python3 -m watercoupler.py  3  AdgdA  Stream.prj  fort
```
for instance, where `<num_procs>` is the number of MPI processes to be used.


## Authors

* **Gajanan Choudhary** - [website](https://users.oden.utexas.edu/~gajanan/)


## License

Water Coupler is distributed under the
[BSD 3-Clause "New" or "Revised" license](LICENSE). Note, however, that some of
the external dependencies of this software are proprietary/closed-source, which
cannot and should not be distributed with this software.


## Acknowledgments

* [f2py](https://numpy.org/doc/stable/f2py/) documentation
* [ctypes](https://docs.python.org/3/library/ctypes.html) documentation
* [Stackoverflow](https://stackoverflow.com/) community

