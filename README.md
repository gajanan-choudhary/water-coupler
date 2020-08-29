# Water Coupler - Python coupler for ADCIRC and GSSHA

Water Coupler is a Python software for coupling ADvanced CIRCulation
([ADCIRC](http://adcirc.org/)) and Gridded Surface Subsurface Hydrologic
Analysis ([GSSHA](https://www.gsshawiki.com/)). Coupling with other software may
be added in the future. The code is intended to run in serial as well as
parallel.


## Getting Started

### Dependencies

* [Python 2.7](https://www.python.org/downloads/release/python-2718/) - for now.
* [NumPy](https://numpy.org/)
* ADCIRC shared library   : `libadcpy.so`
* ADCIRC python interface : `pyadcirc.so`
* GSSHA shared library    : `libgssha.so`
* GSSHA python interface  : `gsshapython`

### Installing

After setting up the prerequisites, open `water-coupler/__init__.py` and
give the full path to the directory that contains `pyadcirc.so` and to the
`gsshapython` directory. Open `water-coupler/__main__.py` and add the full path
to the directory containing the `water-coupler` folder.

### Running tests

Currently, no automated tests have been enabled for `water-coupler`.


## Using the project

Suppose you want to run a coupled ADCIRC-GSSHA simulation, with ADCIRC files
named `fort.*` and GSSHA files named `Stream*`, including the project file
`Stream.prj`. Copy the ADCIRC and GSSHA input files in a single directory. Copy
or add a symlink/shortcut to `water-coupler/__main__.py` into this directory,
naming it as, say, `watercoupler.py` and run the file. Run this file with
command line arguments as follows.
 - Argument 1: Boundary string ID of the ADCIRC model that is being coupled,
 - Argument 2: One of the following coupling type identifiers,
   * `Adg`   - One-way coupling with ADCIRC driving GSSHA,
   * `gdA`   - One-way coupling with GSSHA driving ADCIRC,
   * `AdgdA` - Two-way coupling with ADCIRC "driving" (staying ahead of) GSSHA,
   * `gdAdg` - Two-way coupling with GSSHA "driving" (staying ahead of) ADCIRC,
 - Argument 3: Name of GSSHA Project file, e.g., `Stream.prj`, and
 - Argument 4: Name of ADCIRC Project file, e.g., `fort`.
For instance, the Linux/Unix workflow goes as follows.
```bash
mkdir sample-sim
cd sample-sim
cp <path_to_ADCIRC_input_files>/fort.* .
cp <path_to_GSSHA_input_files>/Stream* .
cp <path_to_water-coupler_folder>/__main__.py watercoupler.py

python watercoupler.py \
    <ADCIRC model coupled boundary> \
    <Coupling type identifier> \
    <GSSHA project file name> \
    <ADCIRC project file name without extension>
```

For parallel runs when ADCIRC has been compiled in parallel using OpenMPI, use
```
mpirun  -np  <num_procs>  python  watercoupler.py  3  AdgdA  Stream.prj  fort
```
where `<num_procs>` is the number of processors you want to use.


## Authors

* **Gajanan Choudhary** - [website](https://users.oden.utexas.edu/~gajanan/)


## License

Water Coupler is distributed under the
[BSD 3-Clause "New" or "Revised" license](LICENSE). Note, however, that some of
the external dependencies of this software are proprietary/closed-source, which
cannot and should not be distributed with this software.


## Acknowledgments

* [f2py](https://numpy.org/doc/stable/f2py/) documentation
* [ctypes](https://docs.python.org/2.7/library/ctypes.html) documentation
* [Stackoverflow](https://stackoverflow.com/) community

