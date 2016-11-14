# GCMStoolbox
Tools for data analysis on GC-MS datafiles


## Prerequisites

Python v2.x


## convert.py: convert AMDIS files (*.msl, *.csl, *.isl) to a NIST MS SEARCH file (*.msp)

```
 ********************************************************************************
 * GCMStoolbox - a set of tools for GC-MS data analysis                         *
 *   Author:  Wim Fremout / Royal Institute for Cultural Heritage (12 Nov 2016) *
 *   Licence: GNU GPL version 3.0                                               *
 *                                                                              *
 * CONVERT:                                                                     *
 *   convert AMDIS files (*.msl, *.csl, *.isl) to a NIST MS SEARCH file (*.msp) *
 *                                                                              *
 ********************************************************************************

Usage: convert.py [options] INFILES

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -o OUTFILE, --outfile=OUTFILE
                        output file name
  -a, --append          append to output file
  -e, --elinc           Special formatting for ELinC data. Extra parameters
                        are retrieved from the structured file names and are
                        used to set custom MSP fields, adapted spectrum names
                        and sources

```
