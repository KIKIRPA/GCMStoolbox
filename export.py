#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import ntpath
import json
from collections import OrderedDict
from glob import glob
from optparse import OptionParser, OptionGroup
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (" + gcmstoolbox.date + ") *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* EXPORT:                                                                     *")
  print(  "*   export the GCMStoolbox data file (JSON) into NIST MS SEARCH format (.msp) *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")


  ### OPTIONPARSER
  
  usage = "usage: %prog [options] OUTFILE"
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose", help="Be very verbose [not default]", action="store_true", dest="verbose", default=False)
  parser.add_option("-i", "--infile",  help="Input file name [default: gcmstoolbox.json]", action="store", dest="infile", type="string", default="gcmstoolbox.json")
  parser.add_option("-m", "--mode",    help="Mode: auto|spectra|group|components [default:auto]", action="store", dest="mode", type="string", default="gcmstoolbox.json")
  
  (options, args) = parser.parse_args()

  ### ARGUMENTS AND OPTIONS
  
  cmd = " ".join(sys.argv)
  
  if options.verbose: print("Processing import files and options")

  # check output file
  if len(args) == 0:
    print("  !! No output file name given\n")
    exit()
  elif len(args) != 1:
    print("  !! Too many arguments. A single output file name can be given.\n")
    exit()
  else:
    outFile = args[0]

  # check and read input file
  if not os.path.isfile(options.infile):
    print("  !! " + options.infile + " was not found.\n")
    exit()
  with open(options.infile,'r') as fh:
    data = json.load(fh, object_pairs_hook=OrderedDict)

  if options.verbose:
    print(" => GCMStoolbox file: " + options.infile)
    print(" => output msp file:  " + outFile + "\n")
    
  # add administration to specta[0] (info) TODO
  #data['info']['cmds'].append(" ".join(sys.argv))


  ### WRITE FILE
  print("Processing mass spectra")
  with open(outFile, "w") as fh:
    
    # mode: SPECTRA
    # init progress bar
    if not options.verbose: 
      j = 0
      k = len(data['spectra'])
      gcmstoolbox.printProgress(j, k)
    
    for name, spectrum in data['spectra'].items():
      writespectrum(fh, name, spectrum, options.verbose)
    
      # adjust progress bar
      if not options.verbose: 
        j += 1
        gcmstoolbox.printProgress(j, k)  
        
  print("\nFinalised. Wrote " + outFile + "\n")
  exit()
    
  
  
  
def writespectrum(fh, name, sp, verbose = False):
  # write the spectrum to the file handle line by line in NIST MSP format
  # don't mind to much about the order of the lines; we start with Name, and end with NumPeaks and the spectral data

  # build comments, while removing fields that don't belong in the msp
  comments = ""
  list = ['Sample', 'Resin', 'AAdays', 'Color', 'PyTemp', 'OR', 'IS', 'RA']
  for l in list:
    val = sp.pop(l, False)
    if val:
      comments += l + "=" + val.replace(" ", "_") + " "
  if "RI" in sp:
    comments += "RI=" + sp['RI'] + " "
  if "RT" in sp:
    comments += "RT=" + sp['RT']
  
  # remove other fields
  numpeaks = sp.pop('Num Peaks')
  xydata   = sp.pop('xydata')
  
  #verbose
  if verbose:
    print("    - Write", name, "in output file")
  
  #start with the Name field (and remove it from the dictionary)
  fh.write('Name: '   + name + "\n")
  
  #then iterate over the remaining items
  for key, value in sp.items():
    fh.write(key + ': ' + value + "\n")
  
  # write comments
  fh.write('Comments: ' + comments.strip() + "\n")
  
  # write NumPeaks
  fh.write('Num Peaks: ' + str(numpeaks) + "\n")
  
  # NIST MSP puts 5 couples on each line
  # 1. iterate over full lines
  div = numpeaks // 5          # we have %div full lines
  for i in range(div):         
    line = ""  
    for j in range(5): 
      x, y = xydata.popitem(last = False)
      line = line + str(x) + " " + str(y) + "; "
    fh.write(line.rstrip(" ") + "\n")
  # 2. iterate over the last incomplete line
  mod = numpeaks % 5           # the last line will have mod couples
  if mod > 0:
    line = ""
    for i in range(mod):
      x, y = xydata.popitem(last = False)
      line = line + str(x) + " " + str(y) + "; "
    fh.write(line.rstrip(" ") + "\n")
  fh.write("\n")



if __name__ == "__main__":
  main()
