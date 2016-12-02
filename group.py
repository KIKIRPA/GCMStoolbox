#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from glob import glob
from optparse import OptionParser, OptionGroup
import json

#globals
spectra = {}  #dictionary of all spectra with the groups to which they belong
groups = {}   #dictionary of groups
doubles = {}  #dictionary of groups of possibly the same component
i = 1         #group or component counter
j = 1         #spectra counter

def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (2 Dec 2016)  *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* GROUP:                                                                      *")
  print(  "*   Search groups in a NIST search of a large dataset against itself          *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  shortdescr = ("Search for groups of the same mass spectra in a large dataset by using\n"
                "NIST search results (generated by MSpepsearch) of the dataset against\n"
                "itself. Search hits can be optionally reduced by applying a retention index\n"
                "window.")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options] INFILE"
  parser = OptionParser(usage, version="%prog 0.2.1")
  parser.add_option("-v", "--verbose", help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-o", "--outfile", help="Output file name", action="store",      dest="outfile", type="string")
  parser.add_option("-r", "--ri",      help="Apply RI window (default [0]: no RI filter)",  action="store", dest="ri", type="float", default=0)
  parser.add_option("-D", "--discard", help="Discard hits without RI",  action="store_true", dest="discard", default=False)
  parser.add_option("-m", "--match",   help="Apply RI window (default [0]: no RI filter)", action="store", dest="minmf", type="int", default=0)
  parser.add_option("-n", "--reverse", help="Apply RI window (default [0]: no RI filter)", action="store", dest="minrmf", type="int", default=0)
  parser.add_option("-Y", "--merge",   help="Merge all overlapping groups into a single component", action="store_true", dest="merge", default=False)
  (options, args) = parser.parse_args()

  ### ARGUMENTS

  if options.verbose: print("Processing arguments")

  if len(args) == 0:
    exit()

  # make a list of input files
  inFiles = []
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
  if numInFiles != 1:
    parser.error("There should be exactly one input file.")
    exit()
  else:
    inFile = inFiles[0]
    
  if options.outfile != None:
    outFile = options.outfile
  else:
    outFile = "groups.json"

  # read mspepsearch results and create the spectra dictionary (couples of "spectrum name : group number") --> spectra dict
  readmspepsearch(inFile, options.ri, options.discard, options.minmf, options.minrmf, options.verbose)
  # find groups --> groups dict
  groupByComponent(options.verbose)
  # merge groups that may be the same component (non-crosslinked matches)
  if options.merge:
    mergeGroups(options.verbose)    
  
  # make output file
  handle = open(outFile, "w")
  handle.write(json.dumps(groups, indent=2))
  handle.close()
  print("\nWritten " + outFile)
  
  print("\nSTATISTICS")
  print("  - Number of mass spectra:      " + str(j - 1))
  print("  - Number of groups/components: " + str(i - 1))
  if not options.merge:
    print("  - Groups that may be the same component: (use -Y to merge)")
    #doubles_sortedkeys = sorted(doubles.keys())
    for key in sorted(doubles.keys()):
      print("      - " + ", ".join(str(d) for d in sorted(doubles[key])))
  else:
    print("  - Number of groups/components after merging non-crosslinked matches: " + str(len(groups)))
  print("  - Number of hits per group/component:")
  groupStatistics(options.verbose)  
  


def readmspepsearch(inFile, riwindow = 0, discard = False, minMF = 0, minRMF = 0, verbose = False):
  ### ITERATE THROUGH INFILE
  # and generate a dictionary of spectra
  print("\nProcessing file: " + inFile)
  
  global spectra, j
  hits = []     #list of (accepted) hits for each NIST search
  
  with open(inFile,'r') as handle:   #file handle closes itself 
    for line in handle: 
      if line.casefold().startswith('unknown'):
        # first process the previous hits list 
        if len(hits) > 0:
          if verbose: print(" - Unknown: " + unknown)
          processHits(hits, verbose)
        
        # reinit
        j = j + 1
        hits = []
        
        unknown = line.split(": ", 1)[1]
        unknown = unknown.split("Compound in Library Factor = ")[0]
        unknown = unknown.strip()
        
        if riwindow > 0:
          unknownRI = extractRI(unknown)
        else:
          unknownRI = 0
      
      elif line.casefold().startswith('hit'):
        # dissect the "hit" line
        line = line.split(": ", 1)[1]
        parts = line.split(">>; ")     # the possibility of having semicolons inside the sample name makes this more complex
        hit = parts[0].replace("<<", "").strip()
        
        if riwindow > 0:
          hitRI = extractRI(hit)
        else:
          hitRI = 0
        
        hitMF, hitRMF, temp = parts[2].split("; ", 2)
        hitMF = int(hitMF.replace("MF: ", "").strip())
        hitRMF = int(hitRMF.replace("RMF: ", "").strip())
        
        # selection based on RIwindow, minMF, minRMF 
        if (riwindow > 0) and (unknownRI > 0) and (hitRI > 0) and (unknownRI - abs(riwindow / 2) <= hitRI <= unknownRI + abs(riwindow / 2)):
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
    if verbose: print(" - Unknown: " + unknown)
    processHits(hits, verbose)



def extractRI(name):
  if "RI=" in name:
    ri = name.split("RI=", 1)[1]
    ri = ri.split(" ", 1)[0]
    ri = float(ri.strip())
  else:
    ri = 0
  return ri



def processHits(hits, verbose = False):
  global spectra, doubles, i
  
  foundgroups = []
  for hit in hits:
    if hit in spectra:
      if spectra[hit] not in foundgroups:
        foundgroups.append(spectra[hit])
  
  if len(foundgroups) == 0:
    group = i
    i = i + 1
    if verbose: print("   new component [C" + str(group) + "]")
  elif len(foundgroups) == 1:
    group = foundgroups[0]
    if verbose: print("   existing component [C" + str(group) + "]")
  else:
    # multiple possible groups; try to compile a list of sets
    # this is not fully waterproof, because it searches only on the lowest component number
    # but probably works in most cases?
    if min(foundgroups) not in doubles:
      doubles[min(foundgroups)] = set(foundgroups)
    else:
      doubles[min(foundgroups)].update(foundgroups)
    group = min(foundgroups)  
    if verbose: print("   !! multiple matched components: " + ', '.join(str(x) for x in foundgroups) + " (Please check!)")

  for hit in hits:
    spectra[hit] = group
    
  return doubles
  
  
  
def groupByComponent(verbose = False):
  print("\nGrouping spectra ...")
  global spectra, groups, i, j
  
  for key, value in spectra.items():
    ri = extractRI(key)
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
        groups[value]["deltaRI"] = groups[value]["maxRI"] - groups[value]["minRI"]
  


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
    if verbose: print(" - " + str(key) + " <= " + ", ".join(doubleset))
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


    
if __name__ == "__main__":
  main()
