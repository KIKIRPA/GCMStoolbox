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
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (3 Jan 2017)  *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* FILTER                                                                      *")
  print(  "*   Reduces the groups json file based on a number of filtering options       *") 
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options] GROUP_JSON_FILE"
  parser = OptionParser(usage, version="%prog 1.0")
  parser.add_option("-v", "--verbose",    help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-o", "--outfile",    help="Output file name", action="store", dest="outfile", type="string")
  group = OptionGroup(parser, "CRITERIUM 1", "Filter out groups based on group number")
  group.add_option("-g", "--group",       help="Group number [default: 0], multiple instances can be defined", action="append", dest="group", type="string")
  parser.add_option_group(group)
  group = OptionGroup(parser, "CRITERIUM 2", "Filter out groups on the number of spectra in a group")
  group.add_option("-c", "--count",      help="Minimal number of spectra per group", action="store", dest="count", type="int")
  parser.add_option_group(group)
  group = OptionGroup(parser, "CRITERIUM 3", "Filter out groups based on the presence of a chosen m/z")
  group.add_option("-m", "--mass",       help="m/z value, multiple instances can be defined", action="append", dest="mass", type="int")
  group.add_option("-M", "--percent",    help="Minimal relative intensity of a m/z value [default: 90]", action="store", dest="percent", type="int", default=90)
  group.add_option("-s", "--sourcefile", help="Data msp file name [default: converted.msp]", action="store",  dest="source", type="string", default="converted.msp")
  parser.add_option_group(group)
  (options, args) = parser.parse_args()
  
  ### ARGUMENTS

  if options.verbose: print("Processing arguments...")

  # input file
  if len(args) == 0: 
    if   os.path.isfile("groups_merged.json"): inFile = "groups_merged.json"
    elif os.path.isfile("groups.json"):        inFile = "groups.json"
    else: 
      print("\n!! GROUP_JSON_FILE not found.")
      exit()
  elif len(args) >= 2:
    print("\n!! There should be exactly one GROUP_JSON_FILE.")
    exit()
  elif os.path.isfile(args[0]):
    inFile = args[0]
  else:
    print("\n!! GROUP_JSON_FILE not found.")
    exit()
    
    
  #criterium flags
  c1 = False if options.group is None else True  #CRITERIUM3: group numbers to be removed
  c2 = False if options.count is None else True  #CRITERIUM1: minimal spectrum count per group 
  c3 = False if options.mass is None  else True  #CRITERIUM2: minimal intensity of choses m/z values

  if not (c1 or c2 or c3):
    print("\n!! No criteria selected. Nothing to do.")
    exit()

  #citerium 3 args
  if c3:
    # source file
    if not os.path.isfile(options.source):
      print("DATA FILE (msp) not found.\n")
      exit()
    
  # output file
  if options.outfile != None:
    outFile = options.outfile
  else:
    outFile = os.path.splitext(os.path.basename(inFile))[0] + "_filtered" + os.path.splitext(inFile)[1]

    
  ### INITIALISE
  with open(inFile,'r') as fh:    
    groups = json.load(fh)

  candidates = set(groups.keys())
  # candidates for removal; each criterium will remove those groups that should be kept
  # since we iterate through a set that will be smaller after each criterium, we'll do the
  # most time-consuming criteria last
  
  
  ### CRITERIUM 1: GROUP NUMBER
  if c1:
    removegroups = list(str(g) for g in options.group)
    print("\nCRITERIUM 1: remove groups by group number: " + ", ".join(removegroups))
    if not options.verbose: 
      i = 0
      j = len(candidates)
      gcmstoolbox.printProgress(i, j)
    for c in list(candidates):   # iterate over a copy of the set, so we can remove things from the original while iterating
      if c not in removegroups:
        candidates.discard(c)
        
      # progress bar
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
  
    if options.verbose: 
      print("candidates for removal:")
      if len(candidates) == 0:
        print("  none")
      else:
        print(tabulate(candidates))

  
  ### CRITERIUM 2: SPECTRUM COUNT
  if c2:
    print("\nCRITERIUM 2: remove groups with less than " + str(options.count) + " spectra...")
    if not options.verbose: 
      i = 0
      j = len(candidates)
      gcmstoolbox.printProgress(i, j)
    for c in list(candidates):   # iterate over a copy of the set, so we can remove things from the original while iterating
      if groups[c]["count"] >= options.count:  #remove from candidates = keep group
        candidates.discard(c)
        
      # progress bar
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
  
    if options.verbose: 
      print("candidates for removal:")
      if len(candidates) == 0:
        print("  none")
      else:
        print(tabulate(candidates))




  ### CRITERIUM 3: RUBBISH PEAK SEARCH
  if c3:
    print("\nCRITERIUM 3: remove groups with m/z value " + ", ".join(str(m) for m in options.mass))
    
    # make a list of all spectra to retrieve
    splist = []
    for c in list(candidates):
      splist.extend(groups[c]['spectra'])
      
    # read spectra from msp file
    print("  Retrieve spectra from the msp file")
    spectra = {}
    if not options.verbose:
      i = 0
      j = len(splist)
      gcmstoolbox.printProgress(i, j)
    with open(options.source,'r') as fh:
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
    
    # process candidates
    print("  Process group spectra")
    if not options.verbose: 
      i = 0
      j = len(candidates)
      gcmstoolbox.printProgress(i, j)
    for c in list(candidates):
      # read the spectra in this group
      groupspectra = []
      for sp in groups[c]['spectra']:
        groupspectra.append(spectra[sp])
      
      # if more than one spectrum, make sumspectrum
      if len(groupspectra) > 1:
        sp = gcmstoolbox.sumspectrum(*groupspectra)
      else:
        sp = groupspectra[0]
        
      # check masses
      remove = False     
      maxval = max(sp['xydata'].values())
      for m in options.mass:
        if m in sp['xydata']:
          if sp['xydata'][m] > (maxval * 0.01 * options.percent):     #remove group
            if options.verbose:
              print(" --> G" + c + " m/z=" + str(m) + " y-value=" + str(sp['xydata'][m]) + " threshold=" + str(maxval * 0.01 * options.percent))
            remove = True

      # final decission
      #if a group is tagged for removal, we need to keep it in the candidates set! if it is not tagged for removal, we eliminate it as a candidate
      if not remove:  
        candidates.discard(c)
        
      # progress bar
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
      
    if options.verbose: 
      print("candidates for removal:")
      if len(candidates) == 0:
        print("  none")
      else:
        print(tabulate(candidates))
    
        
  ### UPDATE GROUPS AND WRITE IT AS JSON
  print("\nRemoving groups that do not meet the criteria...")
  print("  - initial number of groups:       " + str(len(groups)))
  print("  - number of groups to be removed: " + str(len(candidates)))
  
  for c in candidates:
    del groups[c]
  print("  - new number of groups          : " + str(len(groups)))
    
  handle = open(outFile, "w")
  handle.write(json.dumps(groups, indent=2))
  handle.close()
  print("\nWritten " + outFile + "\n")
    
  
    
    
def tabulate(words, termwidth=79, pad=3):
  words = sorted(int(x) for x in words)
  words = list(str(x) for x in words)
  width = len(max(words, key=len)) + pad
  ncols = max(1, termwidth // width)
  nrows = (len(words) - 1) // ncols + 1
  table = []
  for i in range(nrows):
    row = words[i::nrows]
    format_str = ('%%-%ds' % width) * len(row)
    table.append(format_str % tuple(row))
  return '\n'.join(table)



    
if __name__ == "__main__":
  main()
