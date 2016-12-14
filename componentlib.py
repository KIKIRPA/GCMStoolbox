#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from glob import glob
from optparse import OptionParser, OptionGroup
import json
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (12 Dec 2016) *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* COMPONENTLIB                                                                *")
  print(  "*   Makes a NIST msp file with components as defined in the groups json file  *") 
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options] SOURCE_MSP_FILE GROUP_JSON_FILE"
  parser = OptionParser(usage, version="%prog 0.1")
  parser.add_option("-v", "--verbose",    help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("--debug",            help="Debug version; only runs on 5 first groups", action="store_true", dest="debug", default=False)
  parser.add_option("-c", "--cnumber",    help="Start number for component numbers", action="store", dest="c", type="int" , default=1)
  parser.add_option("-p", "--preserve",   help="Preserve group numbers", action="store_true", dest="preserve", default=False)
  parser.add_option("-o", "--outfile",    help="Output file name", action="store", dest="outfile", type="string", default="componentlib.msp")
  (options, args) = parser.parse_args()

  ### ARGUMENTS

  if options.verbose: print("Processing arguments...")

  # preserve and c number flags cannot be used together
  if options.preserve and (options.c != 1):
    print("\n!! The options -c (--cnumber) and -p (--preserve) cannot be used together.")
    exit()

  # input file
  if len(args) == 0: #exit without complaining
      exit()
  elif len(args) != 2:
    print("\n!! This program should have two arguments: firstly the SOURCE_MSP_FILE and secondly the GROUP_JSON_FILE")
    exit()
  else:
    if os.path.isfile(args[0]):
      sourceFile = args[0]
    else:
      print("\n!! SOURCE_MSP_FILE '" + args[0] + "' not found.")
      exit()
      
    if os.path.isfile(args[1]):
      with open(args[1],'r') as fh:    
        groups = json.load(fh)
    else:
      print("\n!! GROUP_JSON_FILE '" + args[1] + "' not found.")
      exit()  
  
  
  ### READ SPECTRA
  
  # make a list of spectra that need to be fetched
  splist = []
  for group in groups.values():
    splist.extend(group['spectra'])
  
  # stdOut
  print("\nRead the required data from " + sourceFile)
  if not options.verbose: 
    i = 0
    j = len(splist)
    gcmstoolbox.printProgress(i, j)

  # read spectra from msp file
  spectra = {}
  with open(sourceFile,'r') as fh:
    while True:
      sp = gcmstoolbox.readspectrum(fh, verbose=options.verbose, match=splist)
      if sp == "eof":
        break
      elif sp != "no match":  # in other words: when we found a matching spectrum
        spectra[sp['Name']] = sp
        # progress bar
        if not options.verbose: 
          i += 1
          gcmstoolbox.printProgress(i, j)


  ### MAKE SUM SPECTRA
  
  # stdOut
  print("\nBuilding component library")
  i = 0  # we'll use this both for the progress bar and for the component number (i + options.c, if options.preserve is false)
  if not options.verbose: 
    j = len(groups.keys())
    gcmstoolbox.printProgress(i, j)
  
  with open(options.outfile,'w') as fh:
    for g in sorted(int(x) for x in groups.keys()):
      # group or component numbering:
      if not options.preserve: c = i + options.c
      else:                    c = g 
      
      # collect the spectra
      groupspectra = []
      for s in groups[str(g)]['spectra']:
        groupspectra.append(spectra.pop(s))
      
      # if more than one spectrum, make sumspectrum
      if len(groupspectra) > 1:
        sp = gcmstoolbox.sumspectrum(*groupspectra, name="C" + str(c))
      else:
        sp = groupspectra[0]
          
      # TODO rebuild the spectra metadata (and change for single spectra things)
      # TODO make resumé!
      
      # write spectrum
      gcmstoolbox.writespectrum(fh, sp, options.verbose)
      
      # progress bar
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
        



    
if __name__ == "__main__":
  main()
