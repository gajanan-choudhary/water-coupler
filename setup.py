#!/usr/bin/env python
import os
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

watercoupler_cmds = ['watercoupler = watercoupler.__main__:main']

setup(
    name='watercoupler',
    version='0.1.0',
    description='Program for coupling hydrodynamic and hydrologic software',
    keywords='Coupling, hydrologic, hydrodynamic, ADCIRC, GSSHA',
    long_description=readme,
    author='Gajanan Choudhary',
    author_email='gajananchoudhary91@gmail.com',
    url='https://github.com/gajanan-choudhary/water-coupler',
    license=license,
    packages=find_packages(exclude=('tests', 'doc')),
    entry_points={'console_scripts': watercoupler_cmds},
    package_dir={'': '.'},
    package_data={'': []},
)
