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
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (3 Jan 2017)  *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* CONVERT:                                                                    *")
  print(  "*   convert AMDIS files (.msl, .csl, .isl) to a NIST MS SEARCH file (.msp)    *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  shortdescr = ("Converts INFILES MSP file format. Multiple INFILES can be supplied by using\n"
                "wildcards (?,*) and will be converted into one single MSP file. If no OUTFILE is\n"
                "given, either the filename of the single input file will be used, or joined.msp\n"
                "will be used in case of multiple input files.")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options] AMDIS_FILES"
  parser = OptionParser(usage, version="%prog 1.0")
  parser.add_option("-v", "--verbose", help="Be very verbose", action="store_true", dest="verbose", default=False)
  parser.add_option("-o", "--outfile", help="Output file name", action="store", dest="outfile", type="string")
  parser.add_option("-a", "--append",  help="Append to existing output file", action="store_true", dest="append",  default=False)
  parser.add_option("-s", "--specno",  help="Override spectrum numbering, start with I", action="store", dest="i", default=1, type="int")
  parser.add_option("-e", "--elinc",   help="Special formatting for ELinC data. Extra parameters are retrieved from the structured file names and are used to set custom MSP fields, adapted spectrum names and sources", action="store_true", dest="elinc", default=False)
  (options, args) = parser.parse_args()

  ### ARGUMENTS

  if options.verbose: print("Processing INFILES and options")

  # make a list of input files
  inFiles = []
  if len(args) == 0:
    print("\n!!No AMDIS FILES given, trying *.msl in the current directory")
    inFiles.extend(glob("*.msl"))
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
    parser.error("No input files?")
    exit()
  else:
    if options.verbose: print(" => " + str(numInFiles) + " input files")
    
  if options.outfile != None:
    outFile = options.outfile
  elif numInFiles == 1:
    outFile = "converted_" + os.path.splitext(os.path.basename(inFiles[0]))[0] + ".msp"
  else:
    outFile = "converted.msp"

  if options.verbose: print(" => output file: " + outFile + (" [append]" if options.append else ""))

  if options.elinc and options.verbose: print(" => ELinC special formatting is set")
  
  ### OPEN OUTPUT FILE
  
  if options.append:
    if not os.path.isfile(outFile):
      print("SOURCE FILE (msp) not found.\n")
      exit()
    #first read the outfile to know the highest DB#
    i = 0
    with open(outFile,'r') as fho:
      for line in fho:
        if line.casefold().startswith('db#'):
          x = int(line.split(":", 1)[1].strip())
          if x > i: i = x
    i = i + 1
    if i < options.i:
      i = options.i 
    fho = open(outFile, mode='a')
  else:
    fho = open(outFile, mode='w')
    i = options.i # spectrum number
    
  j = i
  
  ### ITERATE THROUGH INFILES
  
  for inFile in inFiles:
    print("\nProcessing file: " + inFile)
    with open(inFile,'r') as fhi:   #file handle closes itself 
      while True:
        # read spectra
        sp = gcmstoolbox.readspectrum(fhi, i, options.verbose)
        if sp == "eof": break   # break from while loop if readspectrum returns False (<= EOF)
        
        # apply special ELinC formatting
        if options.elinc:
          sp = elincize(sp, inFile, verbose=options.verbose)
        
        # write spectrum
        if (options.append) and (i == j):     #if append and first spectrum: start with empty line
          fho.write("\n")
        gcmstoolbox.writespectrum(fho, sp, options.verbose)
        
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
