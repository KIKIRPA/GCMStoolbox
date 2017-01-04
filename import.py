#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from glob import glob
from optparse import OptionParser, OptionGroup
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (" + GCMStoolbox.date + ") *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* IMPORT:                                                                     *")
  print(  "*   import one or more AMDIS (.elu, .msl, .csl, .isl) and NIST MS SEARCH      *")
  print(  "*   (.msp) files and store the mass spectra in GCMStoolbox JSON format        *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")


  ### OPTIONPARSER
  
  usage = "usage: %prog [options] IMPORTFILE1 [IMPORTFILE2 [...]]"
  parser = OptionParser(usage, version="%prog " + GCMStoolbox.version)
  parser.add_option("-v", "--verbose", help="Be very verbose [not default]", action="store_true", dest="verbose", default=False)
  parser.add_option("-o", "--outfile", help="Output file name [default: gcmstoolbox.json]", action="store", dest="outfile", type="string", default="gcmstoolbox.json")
  parser.add_option("-a", "--append",  help="Append to existing json file [not default]", action="store_true", dest="append",  default=False)
  group = OptionGroup(parser, IMPORT OPTIONS", "Special formatting options for the ELinC project")
  group.add_option("-s", "--specno",  help="Override spectrum numbering, start with I [default: 1 (if not append)]", action="store", dest="i", default=1, type="int")
  group.add_option("-n", "--norm",    help="Normalise to a given maximum, 0 to skip normalisation [default=999])", action="store", dest="norm", default=999, type="int")
  group.add_option("--allmodels",     help="For AMDIS .ELU files: import all models [not default]", action="store_true", dest="allmodels", default=False)
  parser.add_option_group(group)
  group = OptionGroup(parser, "ELinC", "Special formatting options for the ELinC project")
  group.add_option("-e", "--elinc",   help="Retrieve parameters from the structured file names [not default]", action="store_true", dest="elinc", default=False)
  parser.add_option_group(group)
  (options, args) = parser.parse_args()

  ### ARGUMENTS AND OPTIONS

  if options.verbose: print("Processing import files and options")

  # make a list of input files
  inFiles = []
  if len(args) == 0:
    print("\nNo imput files?")
    exit()
  else:
    for arg in args:
      inFiles.extend(glob(arg))
  inFiles = list(set(inFiles)) #remove duplicates
  for inFile in inFiles:
    if os.path.isdir(inFile):
      inFiles.remove(inFile)   #remove directories
    else:
      if options.verbose: print(" - input file: " + inFile)

  # number of inFiles; must not be 0
  numInFiles = len(inFiles)
  if numInFiles == 0:
    print("\nNo imput files?")
    exit()
  else:
    if options.verbose: print(" => " + str(numInFiles) + " input files")

  if options.verbose: print(" => output file: " + options.outfile + (" [append]" if options.append else ""))
 
  if options.append:
    if not os.path.isfile(options.outfile):
      print("  !! " + options.outfile + " was not found.\n")
      exit()

    # read file
    with open(options.outfile,'r') as fh:    
      spectra = json.load(fh)

    # check if it is a spectra file (cannot append to groups file)
    info = spectra.pop('info')
    if info['type'] == "spectra": 
      print("  !! Cannot append to a '" + info['type'] + "' type data file.\n")
      exit()
      
    # convert keys (spectra numbers) to int (json converted them to str)
    spectra = {int(key): value for key, value in spectra.items()}
    
    # spectrum number counter
    if max(spectra) < options.i:
      i = options.i
    else:
      i = max(spectra)
  else:
    info{'type': 'spectra'}
    i = options.i # spectrum number
    
  if options.elinc and options.verbose: print(" => ELinC special formatting is set")
 
  
  ### ITERATE THROUGH INFILES

  for inFile in inFiles:
    print("\nProcessing file: " + inFile)
    elu = (os.path.splitext(filename)[1][1:].strip().upper() == 'ELU')  # elu is True for .ELU files, False for others
    with open(inFile,'r') as fh:   #file handle closes itself 
      while True:
        # read spectra
        spectrum = gcmstoolbox.readspectrum(fh, i, norm=options.norm, elu=elu, eluAll=options.allmodels, verbose=options.verbose)
        
        if spectrum == "eof": 
          break   # break from while loop if readspectrum returns False (<= EOF)
        elif spectrum != "no match":
          # apply special ELinC formatting
          if options.elinc:
            spectrum = elincize(sp, inFile, verbose=options.verbose)
          
          # write spectrum
          spectra[i] = spectrum
          
          # increase spectrum number
          i = i + 1
        
  # close output file 
  print("\nFinalised. Wrote " + outFile + "\n")
  fho.close()
  exit



def elincize(sp, inFile, separator = "-", verbose = False):
  # special formatting for ELinC data
  #  - retrieve SAMPLECODE, AGING, COLOR, TEMPPROG from filename
  #      e.g S-BLK0065-8-0B-HymCFresh-160531-480-di-med.msl
  #          | |       | |  |         |      |   |__|________ 7+8 [not used]     AMDIS parameter set
  #          | |       | |  |         |      |_______________ 6   PY PROG        pyrolysis temperature program
  #          | |       | |  |         |______________________ 5   [not used]     analysis date
  #          | |       | |  |________________________________ 4   SAMPLE DESCR   sample description
  #          | |       | |___________________________________ 3   AGING + COLOR  days of artificial aging and sample color
  #          | |_______|_____________________________________ 1+2 SAMPLE CODE    code of the sample glass plate
  #          |_______________________________________________ 0   [not used]         
  #  - build new NAME
  #  - build new SOURCE
  
  #verbose
  if verbose:
    print("    - ELinCize spectrum")
  
  #split filename
  base = os.path.splitext(os.path.basename(inFile))[0] #strip path and extension
  parts = base.split(separator)
  
  if len(parts) < 7:
    print("      ! ELinCize failed: not enough parts in " + base + "\n")
    exit()
  
  #rebuild existing fields
  sp['Name']     = "S" + sp['DB#'] + " RI=" + sp['RI'] + " " + parts[1] + "-" + parts[2] + "-" + parts[3] + "-" + parts[6]
  sp['Source']   = os.path.basename(inFile)
  sp['Comments'] = ('Sample="' + parts[0] + '-' + parts[1] + '-' + parts[2] + '" '
                     + 'RI="' + sp['RI'] + '" RT="' + sp['RT'] + '" '
                     + 'Aging="' + parts[3][:-1] + ' days" '
                     + 'Color="' + ("black" if parts[3][-1:].upper() == "B" else "unpigmented") + '" '
                     + 'Description="' + parts[4] + '" '
                     + 'PyTemp="' + parts[6] + '" '
                    )
    
  return sp


  
    
if __name__ == "__main__":
  main()
