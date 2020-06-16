#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pprint
from collections import OrderedDict
from optparse import OptionParser, OptionGroup
import gcmstoolbox


#globals
data = OrderedDict()
allocations = OrderedDict()  #dictionary of all spectra with the groups to which they belong
doubles = OrderedDict()  #dictionary of groups of possibly the same component


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Version: {} ({})                                             *".format(gcmstoolbox.version, gcmstoolbox.date))
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *")
  print(  "*   Licence: GNU GPL version 3                                                *")
  print(  "*                                                                             *")
  print(  "* GROUP:                                                                      *")
  print(  "*   Search groups in a NIST search of a large dataset against itself          *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  
  ### OPTIONPARSER
  
  usage = "usage: %prog [options] MSPEPSEARCH_FILE"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose", help="Be verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-w", "--veryverbose", help="Be insanely verbose",  action="store_true", dest="veryverbose", default=False)
  parser.add_option("-i", "--jsonin",  help="JSON input file name [default: gcmstoolbox.json]", action="store", dest="jsonin", type="string", default="gcmstoolbox.json")
  parser.add_option("-o", "--jsonout", help="JSON output file name [default: same as JSON input file]", action="store", dest="jsonout", type="string")
  
  group = OptionGroup(parser, "RETENTION INDEX GROUPING CRITERIUM", "Only select matching mass spectra that have a retention index matching an RI window around the RI of the unknown spectrum.\n[RIwindow] = [RIfixed] + [RIfactor] * RI\nNote: if both RIfixed and RIfactor are zero, no retention based grouping will be applied.")
  group.add_option("-r", "--rifixed",  help="Apply an RI window with fixed term. [default: 0]",  action="store", dest="rifixed", type="float", default=0)
  group.add_option("-R", "--rifactor", help="Apply an RI window with RI-dependent factor [default: 0]",  action="store", dest="rifactor", type="float", default=0)
  group.add_option("-D", "--discard",  help="Discard hits without RI",  action="store_true", dest="discard", default=False)
  parser.add_option_group(group)

  group = OptionGroup(parser, "NIST MS SEARCH GROUPING CRITERIUM", "(Reverse) match settings are set in and calculated by MSPEPSEARCH. However, the options below can be used to set a minimal MF and/or RMF for the grouping process.")  
  group.add_option("-m", "--match",    help="Apply NIST MS match limit [default: 0]", action="store", dest="minmf", type="int", default=0)
  group.add_option("-n", "--reverse",  help="Apply NIST MS reverse match limit [default: 0]", action="store", dest="minrmf", type="int", default=0)
  parser.add_option_group(group)
  
  #group = OptionGroup(parser, "AMBIGUOUS MATCHES", "Sometimes a spectrum is matched against a series of spectra that are allocated to two or more different groups. By default, these groups are not merged.")
  #group.add_option("-M", "--merge",  help="Merge groups with ambiguous matches", action="store_true", dest="merge", default=False)
  parser.add_option_group(group)
  
  (options, args) = parser.parse_args()

  
  ### ARGUMENTS AND OPTIONS

  global data, allocations, doubles, j, k
  
  cmd = " ".join(sys.argv)
  
  if options.verbose: print("Processing arguments")

  # input file
  if len(args) == 0:
    print(" !! No MSPEPSEARCH file?\n")
    exit()
  elif len(args) >= 2:
    print("  !! Too many arguments. Only one MSPEPSEARCH file can be processed.")
    exit()
  elif os.path.isfile(args[0]):
    inFile = args[0]
  else:
    print("  !! MSPEPSEARCH file " + args[0] +  " not found.")
    exit()
  
  # check and read JSON input file
  data = gcmstoolbox.openJSON(options.jsonin)
    
  # json output 
  if options.jsonout == None: 
    options.jsonout = options.jsonin

  if options.verbose:
    print(" => JSON input file:  " + options.jsonin)
    print(" => JSON output file: " + options.jsonout + "\n")



  ### GROUP LEVEL 1: GENERATE LIST OF HITS PER UNKNOWN
 
  # init progress bar
  print("\nGrouping level 1: processing " + inFile)
  j = 0
  k = len(data['spectra'])
  if not (options.verbose or options.veryverbose) :
    gcmstoolbox.printProgress(j, k)
  
  # read MSPEPSEARCH file line by line, and apply grouping criteria
  hits = []
  grouping1 = OrderedDict()
  with open(inFile,'r') as fh:
    for line in fh:

      if line.casefold().startswith('unknown'):
        # PROCESS PREVIOUS
        if len(hits) > 0:
          grouping1[unknown] = hits

          # report stuff

          if options.veryverbose:
            print(' - "{}": {} retained hits, {} rejected hits:'.format(unknown, len(hits), i-len(hits)))
            print('   [RI window: {} <= RI <= {}]'.format(unknownRI - window, unknownRI + window))
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(hits)
          elif options.verbose:
            print(' - "{}": {} retained hits, {} rejected hits'.format(unknown.split()[1], len(hits), i-len(hits)))
          else: 
            gcmstoolbox.printProgress(j, k)

        # START NEW
        i = 0
        j += 1
        hits = []
        unknown = line.split(": ", 1)[1] \
                      .split("Compound in Library Factor = ")[0] \
                      .strip() # spectrum name of the unknown
        
        # if selection on RI: obtain RI and RIwindow    
        if (options.rifixed != 0) or (options.rifactor != 0):
          unknownRI = getRI(unknown)
          window = abs((options.rifixed + (options.rifactor * unknownRI)) / 2)  # HALF window
        else:
          unknownRI = window = 0

      elif line.casefold().startswith('hit'):
        i += 1

        # dissect the "hit" line
        line = line.split(": ", 1)[1]
        parts = line.split(">>; ")     # the possibility of having semicolons inside the sample name makes this more complex
        hit = parts[0].replace("<<", "").strip()
        
        # extract RI, match and reverse match
        hitRI = getRI(hit) if (window != 0) else 0
        hitMF, hitRMF, temp = parts[2].split("; ", 2)
        hitMF = int(hitMF.replace("MF: ", "").strip())
        hitRMF = int(hitRMF.replace("RMF: ", "").strip())
        
        # RI selection: accept if
        # - RIwindow is given and both RI's are present: accept hit when RI falls within the window
        # - RIwindow is given (without discard option) but at least one of the RI's is missing: accept anyway
        # - RIwindow is zero (= RI matching is disabled): accept 
        accept = ( ((window > 0) and (unknownRI > 0) and (hitRI > 0) and (unknownRI - window <= hitRI <= unknownRI + window))
                    or ((window > 0) and (not options.discard) and ((unknownRI == 0) or (hitRI == 0)))
                    or (window == 0)
                  )

        # Match factor selection
        if (options.minmf > 0) and (options.minmf > hitMF):    accept = False
        if (options.minrmf > 0) and (options.minrmf > hitRMF): accept = False
          
        # add to hits (if the hit is accepted)
        if accept: hits.append(hit)
 
      #elif line == "eof": break





  
  
  exit()













def getRI(name):
  global data
  
  if name in data['spectra']:
    if 'RI' in data['spectra'][name]:
      return float(data['spectra'][name]['RI'])
    else:
      return 0
  
  #if the spectrum doesn't exist: ERROR
  else:
    print("\n!! FATAL ERROR: spectrum " + name + " was not found in the GCMStoolbox JSON data file.\n")





 
if __name__ == "__main__":
  main()
