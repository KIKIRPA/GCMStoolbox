#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from collections import OrderedDict
from optparse import OptionParser, OptionGroup
import gcmstoolbox

#globals
spectra = {}  #dictionary of all spectra with the groups to which they belong
groups = {}   #dictionary of groups
doubles = {}  #dictionary of groups of possibly the same component
i = 1         #group counter
j = 1         #spectra counter

def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (" + gcmstoolbox.date + ") *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* GROUP:                                                                      *")
  print(  "*   Search groups in a NIST search of a large dataset against itself          *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  
  ### OPTIONPARSER
  
  usage = "usage: %prog [options] MSPEPSEARCH_FILE"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose", help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-i", "--jsonin",  help="JSON input file name [default: gcmstoolbox.json]", action="store", dest="jsonin", type="string", default="gcmstoolbox.json")
  parser.add_option("-o", "--jsonout", help="JSON output file name [default: same as JSON input file]", action="store", dest="jsonout", type="string")
  
  group = OptionGroup(parser, "RETENTION INDEX GROUPING CRITERIUM", "Only select matching mass spectra that have a retention index matching an RI window around the RI of the unknown spectrum.\n[RIwindow] = [RIfixed] + [RIfactor] * RI\nNote: if both RIfixed and RIfactor are zero, no retention based grouping will be applied.")
  group.add_option("-r", "--rifixed",  help="Apply an RI window with fixed term. [default: 0]",  action="store", dest="riwindow", type="float", default=0)
  group.add_option("-R", "--rifactor", help="Apply an RI window with RI-dependent factor [default: 0]",  action="store", dest="rifactor", type="float", default=0)
  group.add_option("-D", "--discard",  help="Discard hits without RI",  action="store_true", dest="discard", default=False)
  parser.add_option_group(group)

  group = OptionGroup(parser, "NIST MS SEARCH GROUPING CRITERIUM", "(Reverse) match settings are set in and calculated by MSPEPSEARCH. However, the options below can be used to set a minimal MF and/or RMF for the grouping process.")  
  group.add_option("-m", "--match",    help="Apply NIST MS match limit [default: 0]", action="store", dest="minmf", type="int", default=0)
  group.add_option("-n", "--reverse",  help="Apply NIST MS reverse match limit [default: 0]", action="store", dest="minrmf", type="int", default=0)
  parser.add_option_group(group)
  
  group = OptionGroup(parser, "NON-CROSSLINKED MATCHES")
  group.add_option("-Y", "--merge",    help="Merge all overlapping groups into a single group", action="store_true", dest="merge", default=False)
  parser.add_option_group(group)
  
  (options, args) = parser.parse_args()

  
  ### ARGUMENTS AND OPTIONS

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
  
  # JSON in- & output file
  if not os.path.isfile(options.jsonin):
    print("  !! " + jsonin + " was not found.\n")
    exit()
  if options.jsonout = None: 
    options.jsonout = options.jsonin


  ### GROUP

  # read mspepsearch results and create the spectra dictionary (couples of "spectrum name : group number") --> spectra dict
  readmspepsearch(inFile, options.riwindow, options.rifactor, options.discard, options.minmf, options.minrmf, options.merge, options.verbose)
  # find groups --> groups dict
  groupSpectra(options.verbose)
  # merge groups that may be the same component (non-crosslinked matches)
  if options.merge:
    mergeGroups(options.verbose)
  
  # make output file
  handle = open(outFile, "w")
  handle.write(json.dumps(groups, indent=2))
  handle.close()
  print("\nWritten " + outFile)
  
  
  ### STATS + MERGE2
  
  print("\nSTATISTICS")
  print("  - Number of mass spectra: " + str(j - 1))
  print("  - Number of groups:       " + str(i - 1))
  if not options.merge:
    print("  - Groups that may be the same component: (use -Y to merge)")
    #doubles_sortedkeys = sorted(doubles.keys())
    for key in sorted(doubles.keys()):
      print("      - " + ", ".join(str(d) for d in sorted(doubles[key])))
  else:
    print("  - Number of groups after merging non-crosslinked matches: " + str(len(groups)))
  print("  - Number of hits per group:")
  groupStatistics(options.verbose)  
  


def readmspepsearch(inFile, riwindow = 0, rifactor = 0, discard = False, minMF = 0, minRMF = 0, merge = False, verbose = False):
  ### ITERATE THROUGH INFILE
  # and generate a dictionary of spectra
  print("\nProcessing file: " + inFile)
  
  global spectra, j
  hits = []     #list of (accepted) hits for each NIST search
  
  with open(inFile,'r') as handle:   #file handle closes itself 
    for line in handle: 
      if line.casefold().startswith('unknown'):
        # first process the previous hits list [CAUTION: except the last hit list!]
        if len(hits) > 0:
          if verbose: 
            if riwindow > 0: msg = " (RI window: " + str(round(w,2)) + ")"
            else:            msg = ""
            print(" - Unknown: " + unknown + msg)
          processHits(hits, unknown, merge, verbose)
        
        # reinit
        j = j + 1
        hits = []
        
        unknown = line.split(": ", 1)[1]
        unknown = unknown.split("Compound in Library Factor = ")[0]
        unknown = unknown.strip()
        
        if riwindow > 0:
          unknownRI = gcmstoolbox.extractRI(unknown)
          w = riwindow + (rifactor * unknownRI)
        else:
          unknownRI = 0
      
      elif line.casefold().startswith('hit'):
        # dissect the "hit" line
        line = line.split(": ", 1)[1]
        parts = line.split(">>; ")     # the possibility of having semicolons inside the sample name makes this more complex
        hit = parts[0].replace("<<", "").strip()
        
        if riwindow > 0:
          hitRI = gcmstoolbox.extractRI(hit)
        else:
          hitRI = 0
        
        hitMF, hitRMF, temp = parts[2].split("; ", 2)
        hitMF = int(hitMF.replace("MF: ", "").strip())
        hitRMF = int(hitRMF.replace("RMF: ", "").strip())
        
        # selection based on RIwindow, minMF, minRMF 
        if (riwindow > 0) and (unknownRI > 0) and (hitRI > 0) and (unknownRI - abs(w / 2) <= hitRI <= unknownRI + abs(w / 2)):
          # RIwindow is given and both RI's are present: accept hit when RI falls within the window
          accept = True
        elif (riwindow > 0) and (not discard) and ((unknownRI == 0) or (hitRI == 0)):
          # RIwindow is given (without discard option) but at least one of the RI's is missing: accept anyway
          accept = True
        elif (riwindow == 0):
          # RIwindow is zero (= RI matching is disabled): accept
          accept = True
        else:
          accept = False
        
        if (minMF > 0) and (minMF > hitMF):
          accept = False
        
        if (minRMF > 0) and (minRMF > hitRMF):
          accept = False
          
        # add to hits (if the hit is accepted)
        if accept:
          hits.append(hit)
  
  #process the last unknown
  if len(hits) > 0:
    if verbose: 
      if riwindow > 0: msg = " (RI window: " + str(round(w,2)) + ")"
      else:            msg = ""
      print(" - Unknown: " + unknown + msg)
    processHits(hits, unknown, merge, verbose)




def processHits(hits, unknown, merge = False, verbose = False):
  global spectra, doubles, i
  
  foundgroups = []
  for hit in hits:
    if hit in spectra:
      if verbose: print("   -> hit: " + hit +  " -> G" + str(spectra[hit]))
      if spectra[hit] not in foundgroups:
        foundgroups.append(spectra[hit])
    else:
      if verbose: print("   -> hit: " + hit +  " -> not attributed yet")
  
  if len(foundgroups) == 0:
    group = i
    i = i + 1
    if verbose: print("   new group [G" + str(group) + "]")
  elif len(foundgroups) == 1:
    group = foundgroups[0]
    if verbose: print("   existing group [G" + str(group) + "]")
  else:
    # multiple possible groups; try to compile a list of sets
    # this is not fully waterproof, because it searches only on the lowest group number
    # but probably works in most cases?
    if min(foundgroups) not in doubles:
      doubles[min(foundgroups)] = set(foundgroups)
    else:
      doubles[min(foundgroups)].update(foundgroups)
    #group to attribute the hits to the group to which the unknown is allready attributed
    #and if the unknown is not yet attributed, or in case of merge: to the lowest group
    if (not merge) and (unknown in spectra):
      group = spectra[unknown]
    else:
      group = min(foundgroups)  
    if verbose: 
      print("   !! multiple matched groups: " + ', '.join(str(x) for x in foundgroups) + " (Please check!)")
      if not merge: print("      non-attributed spectra are now G" +  str(group))
      else:         print("      ALL spectra are now (re)attributed to G" +  str(group) + " (merge level 1)")

  for hit in hits:
    if (hit not in spectra) or merge:   # if merge=true :  first level of merging
      spectra[hit] = group

  
  
  
def groupSpectra(verbose = False):
  print("\nGrouping spectra ...")
  global spectra, groups, i, j
  
  for key, value in spectra.items():
    ri = gcmstoolbox.extractRI(key)
    if value not in groups:
      # initialise the group
      groups[value] = {"spectra": [key], "count": 1, "minRI": ri, "maxRI": ri, "deltaRI": 0}
    else:
      # add spectrum to the group
      groups[value]["spectra"].append(key)
      groups[value]["count"] += 1
      if ri != 0:
        if (groups[value]["minRI"] == 0) or (groups[value]["minRI"] > ri):
          groups[value]["minRI"] = ri
        if (groups[value]["maxRI"] == 0) or (groups[value]["maxRI"] < ri):
          groups[value]["maxRI"] = ri
        groups[value]["deltaRI"] = round(groups[value]["maxRI"] - groups[value]["minRI"], 2)
  


def groupStatistics(verbose):
  global groups
  
  # make stats
  stats = {}
  for n, group in groups.items():
    if group["count"] in stats:
      stats[group["count"]] += 1
    else:
      stats[group["count"]] = 1
  
  # write stats
  if verbose:
    for n in range(1, len(stats.keys())):
      if   n < 10 : spacer = "  "
      elif n < 100: spacer = " "
      else:         spacer = ""
      if n in stats:
        print("      - [" + spacer + str(n) + "] " + str(stats[n]))
  else:
    if 1 in stats: print("      - [      1] " + str(stats[1]))
    if 2 in stats: print("      - [      2] " + str(stats[2]))
    if 3 in stats: print("      - [      3] " + str(stats[3]))
    print("      - [ 4 -  9] " + str(countStats(stats, 4, 9)))
    print("      - [10 - 19] " + str(countStats(stats, 10, 19)))
    print("      - [20 - 39] " + str(countStats(stats, 20, 39)))
    print("      - [40 - 59] " + str(countStats(stats, 40, 59)))
    print("      - [60 - 79] " + str(countStats(stats, 40, 79)))
    print("      - [80 - 99] " + str(countStats(stats, 80, 99)))
    print("      - [ >= 100] " + str(countStats(stats, 100)))



def countStats(stats, minimum, maximum = False):
  count = 0
  
  if maximum == False:
    maximum = max(stats.keys(), key=int)
    
  for n in range (minimum, maximum):
    if n in stats: count += stats[n]
    
  return count
  


def mergeGroups(verbose):
  print("\nMerging non-crosslinked groups ...")
  #sorted list of doubles keys (= the lowest value of each of the double sets)
  #in reversed order because there might be overlapping double sets; this way
  #we should recursively remove those overlaps
  tasklist = sorted(doubles.keys(), reverse=True)
  
  for key in tasklist:
    doubleset = doubles[key]
    doubleset.discard(key)
    if verbose: print(" - " + str(key) + " <= " + ", ".join(str(x) for x in doubleset))
    for doubleitem in doubleset:
      if doubleitem in groups:
        #take (and remove) the double out of the groups dict
        d = groups.pop(doubleitem)
        #merge spectra lists without duplicates (convert to set and union them)
        specset = set(groups[key]["spectra"]).union(set(d["spectra"]))
        groups[key]["spectra"] = sorted(list(specset))
        #count
        groups[key]["count"] = len(groups[key]["spectra"])
        #RI things
        if groups[key]["minRI"] > d["minRI"]: 
          groups[key]["minRI"] = d["minRI"]
        if groups[key]["maxRI"] < d["maxRI"]: 
          groups[key]["maxRI"] = d["maxRI"]
        groups[key]["deltaRI"] = d["maxRI"] - d["minRI"]



'''
RECURSIVE SOLUTION

for line
  if startswith unknown:
    readList(fh, unkline, ...)

    
    
def readList(fh, unkline, ...)
  
  init things      #processed = False
  
  for line
    if startswith hit:
      addhit things
    else:
      process     #prevent process from being called twice; if processed = False: processed = process() ?
      if startswith unknown:
        readList(...)   #recursive
  # when EOF, this loop stops, and we'll return to the parent readList(), where the loop also stops? 

  
  
def process()
  return True
  
'''

        
if __name__ == "__main__":
  main()
