#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import csv
from glob import glob
from optparse import OptionParser, OptionGroup
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Version: {} ({})                                             *".format(gcmstoolbox.version, gcmstoolbox.date))
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *")
  print(  "*   Licence: GNU GPL version 3                                                *")
  print(  "*                                                                             *")
  print(  "* SUMSIGNALS:                                                                 *")
  print(  "*   calculates the sum of 'integrated signals' and 'relative amounts' for     *")
  print(  "*   one or more AMDIS *.ELU files                                             *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")


  ### OPTIONPARSER
  
  usage = "usage: %prog [options] ELUFILE1 [ELUFILE2 [...]]"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose", help="Be very verbose [not default]", action="store_true", dest="verbose", default=False)
  parser.add_option("-o", "--out",     help="CSV output file name [default: sumsignals.csv]", action="store", dest="outfile", type="string", default="sumsignals.csv")
  parser.add_option("--allmodels",     help="For AMDIS .ELU files: import all models [not default]", action="store_true", dest="allmodels", default=False)
  
  (options, args) = parser.parse_args()

  ### ARGUMENTS AND OPTIONS
  
  cmd = " ".join(sys.argv)
  
  if options.verbose: print("Processing arguments and options")

  # make a list of input files
  inFiles = []
  if len(args) == 0:
    print(" !! No ELU files?\n")
    exit()
  else:
    for arg in args:
      inFiles.extend(glob(arg))
  inFiles = list(set(inFiles)) #remove duplicates
  for inFile in inFiles:
    if os.path.isdir(inFile):
      inFiles.remove(inFile)   #remove directories
    if (os.path.splitext(inFile)[1][1:].strip().upper() != 'ELU'):
      inFiles.remove(inFile)
    else:
      if options.verbose: print(" - ELU file: " + inFile)

  # number of inFiles; must not be 0
  numInFiles = len(inFiles)
  if numInFiles == 0:
    print(" !! No ELU files?\n")
    exit()
  else:
    if options.verbose: print(" => " + str(numInFiles) + " ELU files")

  if options.verbose: print(" => CSV output file: " + options.jsonout)
 
  
  ### ITERATE THROUGH INFILES
  
  # init progress bar
  print("\nProcessing files")
  if options.verbose:
    print("")
    print(", ".join(["ELU file", "spectra count", "total IS", "total RA"]))
  else:
    j = 0
    k = len(inFiles)
    gcmstoolbox.printProgress(j, k)
  
  # make report file
  with open(options.outfile, 'w', newline='') as fho:
    mkreport = csv.writer(fho, dialect='excel')
    mkreport.writerow(["Intgr.signal (IS)", "The area under the actual extracted component shape expressed in the units of the instrument it was acquired on"])
    mkreport.writerow(["Area (XN)",         "This area is expressed in the units of the instrument that the component was acquired on and is computed by starting from the extracted component shape, but then using any baseline extension that seems reasonable to one or both sides of the actual extracted peak (Extra Width)"])
    mkreport.writerow(["Base peak (AM)",    "The abundance of the most intense mass spectral peak in the deconvoluted spectrum"])
    mkreport.writerow(["Amount (RA)",       "The area of the deconvoluted component (Area) relative to the total ion count for the entire chromatogram, expressed as a percentage"])
    mkreport.writerow("")
    mkreport.writerow(["ELU file", "spectra count", "sum of Integr.signals", "sum of Areas", "sum of Base peaks", "sum of Amounts"])
  
    # process ELU files one by one
    for inFile in inFiles:
      
      # init
      totIS = 0
      totXN = 0
      totAM = 0
      totRA = 0
      toti = 0
      
      # process spectra in a ELU file
      with open(inFile,'r') as fhi:   #file handle closes itself 
        for line in fhi:
          if line.casefold().startswith('name'):
            parts = line.split('|')
            for p in parts:
              if   p.startswith('IS'): specIS = int(p[2:])
              elif p.startswith('XN'): specXN = int(p[2:])
              elif p.startswith('AM'): specAM = int(p[2:])
              elif p.startswith('RA'): specRA = float(p[2:])
              elif p.startswith('OR'): specOR = int(p[2:])  # order number of Amdis models (starts with 1)
            
            if (specOR == 1) or options.allmodels:
              totIS += specIS
              totXN += specXN
              totAM += specAM
              totRA += specRA
              toti += 1
            
      # add report line
      mkreport.writerow([os.path.basename(inFile), toti, totIS, totXN, totAM, "{0:.6f}".format(totRA)])
            
      # adjust progress bar
      if options.verbose: 
        print(", ".join([os.path.basename(inFile), str(toti), str(totIS), str(totXN), str(totAM), "{0:.6f}".format(totRA)]))
      else:
        j += 1
        gcmstoolbox.printProgress(j, k)      
        
        
  ### WRITE SPECTRA JSON 
  
  print("\n => Finalised. Wrote " + options.outfile + "\n")
  exit()



if __name__ == "__main__":
  main()
