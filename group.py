#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
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
  parser.add_option("-v", "--verbose", help="Be very verbose",  action="store_true", dest="verbose", default=False)
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
  
  group = OptionGroup(parser, "AMBIGUOUS MATCHES", "Sometimes a spectrum is matched against a series of spectra that are allocated to two or more different groups. By default, these groups are not merged.")
  group.add_option("-M", "---merge",  help="Merge groups with ambiguous matches", action="store_true", dest="merge", default=False)
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
    

  ### GROUP
 
  # init progress bar
  print("\nProcessing file: " + inFile)
  k = len(data['spectra'])
  if not options.verbose:
    j = 0
    gcmstoolbox.printProgress(j, k)
  
  # open MSPEPSEARCH file, read and interpret it line by line
  i = 1
  with open(inFile,'r') as fh:
    for line in fh:
      for z in range(k):
        if line.casefold().startswith('unknown'):
          line, i = readlist(fh, line, i, options.rifixed, options.rifactor, options.discard, options.minmf, options.minrmf, options.merge, options.verbose)
          
          # update progress bar 
          if not options.verbose: 
            j += 1
            gcmstoolbox.printProgress(j, k)
          
          if line == "eof": break


  ### BUILD GROUPS
  
  print("\nGrouping spectra ...")
  data['groups'] = OrderedDict()

  # init progress bar
  if not options.verbose: 
    j = 0
    k = len(data['spectra'])
    gcmstoolbox.printProgress(j, k)
  

  for s, g in allocations.items():
    g = "G" + str(g)
    buildgroups(data['groups'], g, s)
    
    # adjust progress bar
    if not options.verbose: 
      j += 1
      gcmstoolbox.printProgress(j, k) 
    
  del allocations
        

  ### STATS
  
  stats = OrderedDict()
  stats["spectra"] = len(data['spectra'])
  stats["groups"]  = len(data['groups'])
  if options.merge: stats["merged"]    = [sorted(d) for d in doubles.values()]
  else:             stats["ambiguous"] = [sorted(d) for d in doubles.values()]
  stats["stats"] = groupstats(data['groups'])
  
  print("\nSTATISTICS")
  print("  - Number of mass spectra: " + str(stats["spectra"]))
  print("  - Number of groups:       " + str(stats["groups"]))
  if not options.merge:
    print("  - Groups that may be the same component:")
    for key in sorted(doubles.keys()):
      print("      - " + ", ".join(str(d) for d in sorted(doubles[key])))
  print("  - Number of hits per group:")
  
  if options.verbose:
    lines = groupstats(data['groups'], options.verbose)
  else:
    lines = stats["stats"]
  for l in lines:
    print("      - " + l)
  

  ### UPDATE JSON FILE
  
  if options.verbose: print("\nUpdate JSON output file: " + options.jsonout + "\n")
  data["info"]["mode"] = "group"
  data["info"]["grouping"] = stats
  data["info"]["cmds"].append(cmd)
  gcmstoolbox.saveJSON(data, options.jsonout)     # backup and safe json
  print("\nFinalised. Wrote " + options.jsonout + "\n")
  
  exit()




def readlist(fh, line, i, RIfixed, RIfactor, discard, minMF, minRMF, merge, verbose = False):
  
  global data, allocations, doubles
  
  hits = []
  processed = False
  
  # spectrum name of the unknown
  unknown = line.split(": ", 1)[1]
  unknown = unknown.split("Compound in Library Factor = ")[0]
  unknown = unknown.strip()
  
  # if selection on RI: obtain RI and RIwindow    
  if (RIfixed != 0) or (RIfactor != 0):
    u = getRI(unknown)
    w = RIfixed + (RIfactor * u)
  else:
    u = w = 0
  
  # read next line(s)
  for line in fh:
    if line.casefold().startswith('hit'):
      # dissect the "hit" line
      line = line.split(": ", 1)[1]
      parts = line.split(">>; ")     # the possibility of having semicolons inside the sample name makes this more complex
      hit = parts[0].replace("<<", "").strip()
      
      # extract RI, match and reverse match
      h = getRI(hit) if (w != 0) else 0
      hitMF, hitRMF, temp = parts[2].split("; ", 2)
      hitMF = int(hitMF.replace("MF: ", "").strip())
      hitRMF = int(hitRMF.replace("RMF: ", "").strip())
      
      # RI selection: accept if
      # - RIwindow is given and both RI's are present: accept hit when RI falls within the window
      # - # RIwindow is given (without discard option) but at least one of the RI's is missing: accept anyway
      # - RIwindow is zero (= RI matching is disabled): accept 
      accept = ( ((w > 0) and (u > 0) and (h > 0) and (u - abs(w / 2) <= h <= u + abs(w / 2)))
                 or ((w > 0) and (not discard) and ((u == 0) or (h == 0)))
                 or (w == 0)
               )

      # Match factor selection
      if (minMF > 0) and (minMF > hitMF):    accept = False
      if (minRMF > 0) and (minRMF > hitRMF): accept = False
        
      # add to hits (if the hit is accepted)
      if accept: hits.append(hit)
        
    else:
      if processed == False:
        # process hit list
        if len(hits) > 0:
          if verbose: print(" - Unknown: " + unknown + ((" (RI window: " + str(round(w,2)) + ")") if w > 0 else ""))
      
          foundgroups = []

          for hit in hits:
            if hit in allocations.keys():
              if verbose: print("   -> hit: " + hit +  " -> G" + str(allocations[hit]))
              if allocations[hit] not in foundgroups:
                foundgroups.append(allocations[hit])
            else:
              if verbose: print("   -> hit: " + hit +  " -> not allocated yet")
          
          if len(foundgroups) == 0:
            group = i
            i += 1
            if verbose: print("   new group [G" + str(group) + "]")
          elif len(foundgroups) == 1:
            group = foundgroups[0]
            if verbose: print("   existing group [G" + str(group) + "]")
          else: # multiple possible groups !!!
            # compile a list of sets of duplicates
            if min(foundgroups) not in doubles:
              doubles[min(foundgroups)] = set(foundgroups)
            else:
              doubles[min(foundgroups)].update(foundgroups)

            #group to attribute the hits to the group to which the unknown is allready attributed
            #and if the unknown is not yet attributed, or in case of merge: to the lowest group
            if unknown in allocations:
              group = allocations[unknown]
            else:
              group = min(foundgroups)
              
            if verbose: 
              print("   !! multiple matched groups: " + ', '.join(str(x) for x in foundgroups))
              if not merge: 
                print("      non-allocated spectra are now G" +  str(group))
              else:        
                print("      all spectra are now allocated to G" +  str(group))
                print("      and the other groups were merged.")
            
            #MERGE: remove the chosen group from the foundgroups 
            #and search for all spectra that were allocated to these other groups
            if merge:
              foundgroups.remove(group)
              for other in foundgroups:
                for s, g in allocations.items():
                  if other == g:
                    hits.append(s)

          # allocate
          hits = list(set(hits))  # remove duplicates
          for hit in hits:
            if (hit not in allocations) or merge:   # if merge=true :  first level of merging
              allocations[hit] = group
        
        processed = True  #prevent process from being called twice
        
      if line.casefold().startswith('unknown'):
        return line, i
        
  # when EOF
  return "eof", i





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




def buildgroups(groups, g, s):
  ri = getRI(s)
  
  if g not in groups:
    # initialise the group
    groups[g] = OrderedDict([("spectra", [s]), ("count", 1), ("minRI", ri), ("maxRI", ri), ("deltaRI", 0)])
  
  else:
    # add spectrum to the group
    groups[g]["spectra"].append(s)
    groups[g]["count"] += 1
    
    if ri != 0:
      if (groups[g]["minRI"] == 0) or (groups[g]["minRI"] > ri):
        groups[g]["minRI"] = ri
      if (groups[g]["maxRI"] == 0) or (groups[g]["maxRI"] < ri):
        groups[g]["maxRI"] = ri
      groups[g]["deltaRI"] = round(groups[g]["maxRI"] - groups[g]["minRI"], 2)



def groupstats(groups, verbose = False):
  
  # make stats
  stats = {}
  for n, group in groups.items():
    if group["count"] in stats:
      stats[group["count"]] += 1
    else:
      stats[group["count"]] = 1
  
  # write stats
  lines = []
  if verbose:
    for n in range(1, len(stats.keys())):
      if   n < 10 : spacer = "  "
      elif n < 100: spacer = " "
      else:         spacer = ""
      if n in stats:
        lines.append("[" + spacer + str(n) + "] " + str(stats[n]))
  else:
    if 1 in stats: lines.append("[      1] " + str(stats[1]))
    if 2 in stats: lines.append("[      2] " + str(stats[2]))
    if 3 in stats: lines.append("[      3] " + str(stats[3]))
    lines.append("[ 4 -  9] " + str(countStats(stats, 4, 9)))
    lines.append("[10 - 19] " + str(countStats(stats, 10, 19)))
    lines.append("[20 - 39] " + str(countStats(stats, 20, 39)))
    lines.append("[40 - 59] " + str(countStats(stats, 40, 59)))
    lines.append("[60 - 79] " + str(countStats(stats, 40, 79)))
    lines.append("[80 - 99] " + str(countStats(stats, 80, 99)))
    lines.append("[ >= 100] " + str(countStats(stats, 100)))
    
  return lines
    



def countStats(stats, minimum, maximum = False):
  count = 0
  
  if maximum == False:
    maximum = max(stats.keys(), key=int)
    
  for n in range (minimum, maximum):
    if n in stats: count += stats[n]
    
  return count



 
if __name__ == "__main__":
  main()
