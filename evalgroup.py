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
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (6 Dec 2016)  *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* EVALGROUP                                                                   *")
  print(  "*   Makes a NIST msp file for a selected number of groups/components for      *") 
  print(  "*   evaluation with NIST MS Search                                            *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options] GROUP(S)"
  parser = OptionParser(usage, version="%prog 0.2")
  parser.add_option("-v", "--verbose",    help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-s", "--sourcefile", help="Source msp file name [default: joined.msp]", action="store",  dest="source", type="string", default="joined.msp")
  parser.add_option("-g", "--groupfile",  help="Group json file name [default: groups.json]", action="store",  dest="groups", type="string", default="groups.json")
  parser.add_option("-o", "--outfile",  help="Output file name", action="store",      dest="outfile", type="string")
  (options, args) = parser.parse_args()

  ### INITIALISE MAIN VARS
  
  groupdict = {}    #dictionary of groups with {groupnumber: set of spectra} to be searched in json
  specset = set()   #set of spectra to be searched in msp
  specdict = {}     #dictionary of spectra (metadata and data) taken from msp
  
  ### ARGUMENTS

  if options.verbose: print("Processing arguments...")

  if len(args) == 0:
    print("No arguments")

  # make a dict of groups that should be seached and compiled into a msp
  for arg in args:
    groupdict[int(arg.lower().lstrip("c").strip(","))] = set() #we will fill these with the spectra names corresponding with these groups
  
  # source file
  if not os.path.isfile(options.source):
    print("SOURCE FILE (msp) not found.\n")
    exit()
  
  # source file
  if not os.path.isfile(options.groups):
    print("GROUP FILE (json) not found.\n")
    exit()
    
  # output file
  if options.outfile != None:
    outFile = options.outfile
  else:
    outFile = "evalgroup_" + "_".join(str(x) for x in sorted(groupdict.keys())) + ".msp"
    
  ### EXTRACT SPECTRA NAMES FROM JSON GROUPS FILE
  
  if options.verbose: print("\nProcessing groups file (json)...")

  with open(options.groups,'r') as fh:    
    groups = json.load(fh)
    
  for key in groupdict:
    if (str(key) in groups) and ("spectra" in groups[str(key)]):
      groupdict[key].update(groups[str(key)]["spectra"])
      specset.update(groups[str(key)]["spectra"])
    else:
      print("Group " + str(key) + " not found in " + options.groups)
  
  del groups   #remove this potenially very large variable from memory
  
  ### FIND SPECTRA IN SOURCE FILE
  
  if options.verbose: print("\nReading spectra...")

  with open(options.source,'r') as fh:
    while True:
      sp = gcmstoolbox.readspectrum(fh, verbose=options.verbose, match=list(specset))
      if sp == "eof":
        break
      elif sp != "no match":  # in other words: when we found a matching spectrum
        specdict[sp['Name']] = sp
        specset.discard(sp['Name'])
      
      if len(specset) == 0:   #no need to read the source file further if we have all required spectra
        break
      
  #if not all spectra were obtained from the source file: error!
  if len(specset) != 0:
    print("ERROR Some spectra could not be found in " + options.source + ":")
    print("  - " + "\n  - ".join(specset))
    exit()

  ### COMPILE ALL DATA TOGETHER, ADAPT NAMES, ADD SUM SPECTRA
  
  if options.verbose: print("\nWriting spectra...")
  
  with open(outFile,'w') as fh:
    for group, spectra in groupdict.items():
      sumspectra = [] #list of spectra that will be summed
      prefix = "C" + str(group) + " "
      
      # write individual spectra
      for key in spectra:
        sp = specdict.pop(key)
        sp["Name"] = prefix + sp["Name"] #add group number to spectrum name
        gcmstoolbox.writespectrum(fh, dict(sp), verbose=False)
        sumspectra.append(sp)
      
      # write sum spectra
      prefix = prefix + "sum"
      sp = gcmstoolbox.sumspectrum(*sumspectra, name=prefix)
      gcmstoolbox.writespectrum(fh, sp, verbose=False)


        
    
    
if __name__ == "__main__":
  main()
