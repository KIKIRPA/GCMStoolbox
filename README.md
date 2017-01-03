# GCMStoolbox
Tools for data analysis on GC-MS datafiles


## Prerequisites

Python v3.x


## convert.py: convert AMDIS files to a NIST MS SEARCH file

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (3 Jan 2017)  *
*   Licence: GNU GPL version 3.0                                              *
*                                                                             *
* CONVERT:                                                                    *
*   convert AMDIS files (.msl, .csl, .isl) to a NIST MS SEARCH file (.msp)    *
*                                                                             *
*******************************************************************************

Usage: convert.py [options] AMDIS_FILES

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -o OUTFILE, --outfile=OUTFILE
                        Output file name
  -a, --append          Append to existing output file
  -s I, --specno=I      Override spectrum numbering, start with I
  -e, --elinc           Special formatting for ELinC data. Extra parameters
                        are retrieved from the structured file names and are
                        used to set custom MSP fields, adapted spectrum names
                        and sources
```


## group.py: search groups in batch NIST search results against itself

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (3 Jan 2017)  *
*   Licence: GNU GPL version 3.0                                              *
*                                                                             *
* GROUP:                                                                      *
*   Search groups in a NIST search of a large dataset against itself          *
*                                                                             *
*******************************************************************************

Usage: group.py [options] MSPEPSEARCH_OUTPUT

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -o OUTFILE, --outfile=OUTFILE
                        Output file name
  -r RIWINDOW, --riwindow=RIWINDOW
                        Apply RI window (default [0]: no RI filter)
  -R RIFACTOR, --rifactor=RIFACTOR
                        Apply a factor to make the window dependent on the RI
                        (window = [riwindow] + [rifactor] * RI)
  -D, --discard         Discard hits without RI
  -m MINMF, --match=MINMF
                        Apply RI window (default [0]: no RI filter)
  -n MINRMF, --reverse=MINRMF
                        Apply RI window (default [0]: no RI filter)
  -Y, --merge           Merge all overlapping groups into a single group
```


## evalgroup.py: make a NIST MSP file for one or multiple groups for evaluation

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (3 Jan 2017)  *
*   Licence: GNU GPL version 3.0                                              *
*                                                                             *
* EVALGROUP                                                                   *
*   Makes a NIST msp file for a selected number of groups/components for      *
*   evaluation with NIST MS Search                                            *
*                                                                             *
*******************************************************************************

Usage: evalgroup.py [options] GROUP(S)

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -s SOURCEFILE, --sourcefile=SOURCEFILE
                        Source msp file name [default: converted.msp]
  -g GROUPSFILE, --groupfile=GROUPSFILE
                        Group json file name [default: groups[_merged].json]
  -o OUTFILE, --outfile=OUTFILE
                        Output file name
```


## filter.py: remove groups based on a number of criteria

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (3 Jan 2017)  *
*   Licence: GNU GPL version 3.0                                              *
*                                                                             *
* FILTER                                                                      *
*   Reduces the groups json file based on a number of filtering options       *
*                                                                             *
*******************************************************************************

Usage: filter.py [options] GROUP_JSON_FILE

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -o OUTFILE, --outfile=OUTFILE
                        Output file name

  CRITERIUM 1:
    Filter out groups based on group number

    -g GROUP, --group=GROUP
                        Group number [default: 0], multiple instances can be
                        defined

  CRITERIUM 2:
    Filter out groups on the number of spectra in a group

    -c COUNT, --count=COUNT
                        Minimal number of spectra per group

  CRITERIUM 3:
    Filter out groups based on the presence of a chosen m/z

    -m MASS, --mass=MASS
                        m/z value, multiple instances can be defined
    -M PERCENT, --percent=PERCENT
                        Minimal relative intensity of a m/z value [default:
                        90]
    -s SOURCE, --sourcefile=SOURCE
                        Data msp file name [default: converted.msp]
```

## componentlib.py: make a NIST MSP file of component spectra

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (3 Jan 2017)  *
*   Licence: GNU GPL version 3.0                                              *
*                                                                             *
* COMPONENTLIB                                                                *
*   Makes a NIST msp file with components as defined in the groups json file  *
*                                                                             *
*******************************************************************************

Usage: componentlib.py [options] SOURCE_MSP_FILE GROUP_JSON_FILE

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -c C, --cnumber=C     Start number for component numbers
  -p, --preserve        Preserve group numbers
  -e, --elinc           Special formatting for ELinC data
  -o OUTFILE, --outfile=OUTFILE
                        Output file name [default: componentlib.msp]
```
