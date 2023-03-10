# GCMStoolbox
Tools for data analysis on GC-MS datafiles


## Prerequisites

Python v3.8 or higher


## import.py: import one or more AMDIS (.elu, .msl, .csl, .isl) and NIST MS SEARCH (.msp) files and store the mass spectra in GCMStoolbox JSON format

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Version: 4.0    (21 Jan 2020)                                             *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *
*   Licence: GNU GPL version 3                                                *
*                                                                             *
* IMPORT:                                                                     *
*   import one or more AMDIS (.elu, .msl, .csl, .isl) and NIST MS SEARCH      *
*   (.msp) files and store the mass spectra in GCMStoolbox JSON format        *
*                                                                             *
*******************************************************************************

Usage: import.py [options] IMPORTFILE1 [IMPORTFILE2 [...]]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose [not default]
  -o JSONOUT, --jsonout=JSONOUT
                        JSON output file name [default: gcmstoolbox.json]
  -a, --append          Append to existing json file [not default]

  IMPORT OPTIONS:
    Special formatting options for the ELinC project

    -s I, --specno=I    Override spectrum numbering, start with I [default:
                        1]; the append option may override this
    -n N, --norm=N      Normalise to a given maximum, 0 to skip normalisation
                        [default=999])
    --allmodels         For AMDIS .ELU files: import all models [not default]

  ELinC:
    Special formatting options for the ELinC project

    -e, --elinc         Retrieve parameters from the structured file names
                        [not default]
```


## export.py: export the GCMStoolbox data file (JSON) into NIST MS SEARCH format (.msp)

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Version: 4.0    (21 Jan 2020)                                             *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *
*   Licence: GNU GPL version 3                                                *
*                                                                             *
* EXPORT:                                                                     *
*   export the GCMStoolbox data file (JSON) into NIST MS SEARCH format (.msp) *
*                                                                             *
*******************************************************************************

Usage: export.py [options] MSP_FILE

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose [not default]
  -i JSONIN, --jsonin=JSONIN
                        JSON input file name [default: gcmstoolbox.json]
  -o JSONOUT, --jsonout=JSONOUT
                        JSON output file name [default: same as JSON input
                        file]
  -m MODE, --mode=MODE  Mode: auto|spectra|group|components [default:auto]
  -g GROUP, --group=GROUP
                        Group numbers to export in group mode; multiple
                        instances can be defined
```


## group.py: search groups in batch NIST search results against itself

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Version: 4.0    (21 Jan 2020)                                             *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *
*   Licence: GNU GPL version 3                                                *
*                                                                             *
* GROUP:                                                                      *
*   Search groups in a NIST search of a large dataset against itself          *
*                                                                             *
*******************************************************************************

Usage: group.py [options] MSPEPSEARCH_FILE

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -i JSONIN, --jsonin=JSONIN
                        JSON input file name [default: gcmstoolbox.json]
  -o JSONOUT, --jsonout=JSONOUT
                        JSON output file name [default: same as JSON input
                        file]

  RETENTION INDEX GROUPING CRITERIUM:
    Only select matching mass spectra that have a retention index matching
    an RI window around the RI of the unknown spectrum. [RIwindow] =
    [RIfixed] + [RIfactor] * RI Note: if both RIfixed and RIfactor are
    zero, no retention based grouping will be applied.

    -r RIFIXED, --rifixed=RIFIXED
                        Apply an RI window with fixed term. [default: 0]
    -R RIFACTOR, --rifactor=RIFACTOR
                        Apply an RI window with RI-dependent factor [default:
                        0]
    -D, --discard       Discard hits without RI

  NIST MS SEARCH GROUPING CRITERIUM:
    (Reverse) match settings are set in and calculated by MSPEPSEARCH.
    However, the options below can be used to set a minimal MF and/or RMF
    for the grouping process.

    -m MINMF, --match=MINMF
                        Apply NIST MS match limit [default: 0]
    -n MINRMF, --reverse=MINRMF
                        Apply NIST MS reverse match limit [default: 0]

  AMBIGUOUS MATCHES:
    Sometimes a spectrum is matched against a series of spectra that are
    allocated to two or more different groups. By default, these groups
    are not merged.

    -M, --merge         Merge groups with ambiguous matches
```


## filter.py: remove groups based on a number of criteria

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Version: 4.0    (21 Jan 2020)                                             *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *
*   Licence: GNU GPL version 3                                                *
*                                                                             *
* FILTER                                                                      *
*   Reduces the groups json file based on a number of filtering options       *
*                                                                             *
*******************************************************************************

Usage:

Commands:
  list    Overview of defined filters
           --> usage: filter.py list [options]
  on      Enable filter
           --> usage: filter.py on [options] FILTER_NUMBERS
  off     Disable filter
           --> usage: filter.py off [options] FILTER_NUMBERS
  make    Define a new filter
           --> usage: filter.py make [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -i JSONIN, --jsonin=JSONIN
                        JSON input file name [default: gcmstoolbox.json]
  -o JSONOUT, --jsonout=JSONOUT
                        JSON output file name [default: same as JSON input
                        file]

  MAKE: Filter out groups based on group number:
    -g GROUP, --group=GROUP
                        Group number [default: 0], multiple possible

  MAKE: Filter out groups on the number of spectra in a group:
    -c COUNT, --count=COUNT
                        Minimal number of spectra per group
    -C                  Don't count multiple spectra from the same source

  MAKE: Filter out groups based on the presence of a chosen m/z:
    -m MASS, --mass=MASS
                        m/z value, multiple possible
    -M PERCENT, --percent=PERCENT
                        Minimal relative intensity of a m/z value [default:
                        90]
    -s N, --sum=N       Calculate sumspectra with the N spectra with highest
                        signal, 0 for all [default: 0]
```


## build.py: build a NIST MSP file of component spectra

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Version: 4.0    (21 Jan 2020)                                             *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *
*   Licence: GNU GPL version 3                                                *
*                                                                             *
* BUILD                                                                       *
*   Builds the component spectra                                              *
*                                                                             *
*******************************************************************************

Usage: build.py [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -i JSONIN, --jsonin=JSONIN
                        JSON input file name [default: gcmstoolbox.json]
  -o JSONOUT, --jsonout=JSONOUT
                        JSON output file name [default: same as JSON input
                        file]
  -c C, --cnumber=C     Start number for component numbers
  -p, --preserve        Preserve group numbers
  -s N, --sum=N         Calculate sumspectra with the N spectra with highest
                        signal, 0 for all [default: 0]
```


## report.py: generate a report of categories in a component library

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Version: 4.0    (21 Jan 2020)                                             *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *
*   Licence: GNU GPL version 3                                                *
*                                                                             *
* REPORT                                                                      *
*   Generate CSV report of a component library                                *
*                                                                             *
*******************************************************************************

Usage: report.py [options] REPORT_CSV

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose
  -i JSONIN, --jsonin=JSONIN
                        JSON input file name [default: gcmstoolbox.json]
  -o JSONOUT, --jsonout=JSONOUT
                        JSON output file name [default: same as JSON input
                        file]
  -g GROUPBY, --groupby=GROUPBY
                        Group measurements by categories (eg. Source, Sample,
                        AAdays, Resin...)
```


## sumsignals.py: calculates the sum of areas in ELU files

```
*******************************************************************************
* GCMStoolbox - a set of tools for GC-MS data analysis                        *
*   Version: 4.0    (21 Jan 2020)                                             *
*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *
*   Licence: GNU GPL version 3                                                *
*                                                                             *
* SUMSIGNALS:                                                                 *
*   calculates the sum of 'integrated signals' and 'relative amounts' for     *
*   one or more AMDIS *.ELU files                                             *
*                                                                             *
*******************************************************************************

Usage: sumsignals.py [options] ELUFILE1 [ELUFILE2 [...]]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Be very verbose [not default]
  -o OUTFILE, --out=OUTFILE
                        CSV output file name [default: sumsignals.csv]
  --allmodels           For AMDIS .ELU files: import all models [not default]
```
