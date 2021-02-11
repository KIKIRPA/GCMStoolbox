#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from collections import OrderedDict
from optparse import OptionParser, OptionGroup
from statistics import mean
import gcmstoolbox


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
  parser.add_option("-v", "--verbose", help="Be verbose", action="store_true", dest="verbose", default=False)
  parser.add_option("-w", "--veryverbose", help="Be insanely verbose", action="store_true", dest="veryverbose", default=False)
  parser.add_option("-C", "--conflictfiles", help="Create debug files of conflicting groups at each grouping stage", action="store_true", dest="conflictfiles", default=False)
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
  
  # check and read JSON input file
  data = gcmstoolbox.openJSON(options.jsonin)
    
  # json output 
  if options.jsonout == None: 
    options.jsonout = options.jsonin

  if options.verbose:
    print(" => JSON input file:  " + options.jsonin)
    print(" => JSON output file: " + options.jsonout + "\n")


  ### GROUP STAGE 1: GENERATE LIST OF HITS PER UNKNOWN
 
  # init progress bar
  print("\nGrouping stage 1: Generate lists of hits per unknown")
  print("Processing " + inFile)
  j = 0
  k = len(data['spectra'])
  if not (options.verbose or options.veryverbose) :
    gcmstoolbox.printProgress(j, k)

  # read MSPEPSEARCH file line by line, and apply grouping criteria
  hits = []
  hitRIs = []
  stage1 = OrderedDict()
  with open(inFile,'r') as fh:
    for line in fh:

      if line.casefold().startswith('unknown'):
        # PROCESS PREVIOUS
        if len(hits) > 0:
          stage1[unknown] = OrderedDict()
          stage1[unknown]['spectra'] = hits
          stage1[unknown]['meanRI'] = round(mean(hitRIs), 1)
          stage1[unknown]['minRI'] = round(min(hitRIs), 1)
          stage1[unknown]['maxRI'] = round(max(hitRIs), 1)

          # report stuff
          if options.veryverbose:
            print(' - "{}": {} retained hits, {} rejected hits:'.format(unknown, len(hits), i-len(hits)))
            print('    - RI window: {} <= RI <= {}'.format(
              round(unknownRI - window, 1), 
              round(unknownRI + window), 1)
            )
            for hit in hits:
              print('    - retained hit: {}'.format(hit))
          elif options.verbose:
            print(' - "{}": {} retained hits, {} rejected hits'.format(unknown.split()[1], len(hits), i-len(hits)))
          else: 
            gcmstoolbox.printProgress(j, k)

        # START NEW
        i = 0
        j += 1
        hits = []
        hitRIs = []
        unknown = line.split(": ", 1)[1] \
                      .split("Compound in Library Factor = ")[0] \
                      .strip() # spectrum name of the unknown
        
        # if selection on RI: obtain RI and RIwindow    
        if (options.rifixed != 0) or (options.rifactor != 0):
          unknownRI = getRI(unknown, data['spectra'])
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
        hitRI = getRI(hit, data['spectra']) if (window != 0) else 0
        hitMF, hitRMF, temp = parts[2].split("; ", 2)
        hitMF = int(hitMF.replace("MF: ", "").strip())
        hitRMF = int(hitRMF.replace("RMF: ", "").strip())
        
        # RI selection: accept if
        # - RIwindow is given and both RI's are present: accept hit when RI falls within the window
        # - RIwindow is given (without discard option) but at least one of the RI's is missing: accept anyway
        # - RIwindow is zero (= RI matching is disabled): accept 
        accept = ( 
          ((window > 0) and (unknownRI > 0) and (hitRI > 0) and (unknownRI - window <= hitRI <= unknownRI + window))
          or ((window > 0) and (not options.discard) and ((unknownRI == 0) or (hitRI == 0)))
          or (window == 0)
        )

        # Match factor selection
        if (options.minmf > 0) and (options.minmf > hitMF):    accept = False
        if (options.minrmf > 0) and (options.minrmf > hitRMF): accept = False
          
        # add to hits (if the hit is accepted)
        if accept: 
          hits.append(hit)
          hitRIs.append(hitRI)
 

  ### GROUP STAGE 2: MERGE SIMILAR GROUPS

  # init progress bar
  print("\n\nGrouping stage 2: Merge similar hitlists")
  j = 0
  k = len(stage1)
  if not (options.verbose or options.veryverbose) :
    gcmstoolbox.printProgress(j, k)

  # loop over unkowns
  stage2 = OrderedDict()
  conflicts = []

  for unknown in stage1:
    j += 1

    # skip unknowns that have been grouped previously
    if 'group' in stage1[unknown]:
      if options.veryverbose or options.verbose:
        print(' - "{}": was previously attributed to {}'.format(unknown.split()[0], stage1[unknown]['group']))
      else: 
        gcmstoolbox.printProgress(j, k)
      continue

    # if selection on RI: obtain RI and RIwindow    
    if (options.rifixed != 0) or (options.rifactor != 0):
      meanRI = stage1[unknown]['meanRI']
      window = abs((options.rifixed + (options.rifactor * meanRI)) / 2)  # HALF window
    else:
      meanRI = window = 0

    # things to merge
    ungrouped = set()
    groupIds = set()

    # loop over hits for this unknown
    for hit in stage1[unknown]['spectra']:
      # skip self-hit
      if unknown == hit:
        continue

      # what to do if the hit's group has already been merged with another group??
      if 'group' in stage1[hit]:
        groupId = stage1[hit]['group']
        hitRI = stage2[groupId]['meanRI']
      else:
        groupId = False
        hitRI = stage1[hit]['meanRI']

      # check if the meanRI of the hit's group fits with this meanRI
      accept = ( 
        ((window > 0) and (meanRI > 0) and (hitRI > 0) and (meanRI - window <= hitRI <= meanRI + window))
        or ((window > 0) and (not options.discard) and ((meanRI == 0) or (hitRI == 0)))
        or (window == 0)
      )

      if accept:
        if groupId: groupIds.add(group)
        else:     ungrouped.add(hit)

    # use new or existing stage2 group
    if len(groupIds) == 0:
      # create new group
      groupId = "G" + str(len(stage2) + 1)
      stage2[groupId] = OrderedDict()
      stage2[groupId]['spectra'] = []
      if options.veryverbose or options.verbose:
        print(' - "{}": is attributed to {} (new group)'.format(unknown.split()[0], groupId))
    elif len(groupIds) == 1:
      # use existing group
      groupId = list(groupIds)[0]
      if options.veryverbose or options.verbose:
        print(' - "{}": is attributed to {} (existing group)'.format(unknown.split()[0], groupId))
    else:
      # CONFLICT: multiple possible groups to merge with
      conflicts.append(groupIds)
      groupId = min(groupIds) #take the lowest (arbitrary!!!)
      if options.veryverbose or options.verbose:
        print(' - "{}": is attributed to {} (existing group)'.format(unknown.split()[0], groupId))
        print('   WARNING: GROUPING CONFLICT - multiple matching groups: {}'.format(", ".join(groupIds)))

    # merge results in stage2 dataset (hits from unknown + hits from retained hits)
    # 1. spectra already in stage2[groupId]
    spectra = set(stage2[groupId]['spectra'])
    # 2. spectra from stage1[unknown]
    spectra.update(stage1[unknown]['spectra'])
    stage1[unknown]['group'] = groupId
    del stage1[unknown]['spectra'], stage1[unknown]['meanRI'], stage1[unknown]['minRI'], stage1[unknown]['maxRI']
    # 3. spectra from stage1 hits that are yet ungrouped: only if no conflicts
    #    (in case of conflicts, wait until this is hit is treated as unknown)
    if len(groupIds) <= 1:
      for hit in ungrouped:
        n = len(stage1[hit]['spectra'])
        spectra.update(stage1[hit]['spectra'])
        del stage1[hit]['spectra'], stage1[hit]['meanRI'], stage1[hit]['minRI'], stage1[hit]['maxRI']
        stage1[hit]['group'] = groupId
        if options.veryverbose:
          print('   - adding hitlist from {} ({} spectra)'.format(hit.split()[0], str(n)))
    # 4. store updated spectra list in stage2 group
    stage2[groupId]['spectra'] = list(spectra)

    # (re)calculate mean, min and max RI values for the group
    groupRIs = []
    for hit in stage2[groupId]['spectra']:
      groupRIs.append(getRI(hit, data['spectra']))
    stage2[groupId]['meanRI'] = round(mean(groupRIs), 1)
    stage2[groupId]['minRI'] = round(min(groupRIs), 1)
    stage2[groupId]['maxRI'] = round(max(groupRIs), 1)
    if options.veryverbose:
      print('   - new mean group RI {} (min: {} ; max: {})'.format(
        stage2[groupId]['meanRI'],
        stage2[groupId]['minRI'],
        stage2[groupId]['maxRI']
      ))
    
    # report stuff when not verbose
    if not options.veryverbose and not options.verbose:
      gcmstoolbox.printProgress(j, k)


  ### GROUP STAGE 3: HANDLE MERGE CONFLICTS

  print("\n\nGrouping stage 3: Handle merge conflicts")
  print("Algorithm 'group1': groups-based merging if mean RI's are similar")

  # step 1: collecting sets of conflicting groups

  print(" - Collecting sets of conflicting groups")
  j = 0
  k = len(conflicts)
  gcmstoolbox.printProgress(j, k)

  conflictSets = []

  for conflict in conflicts:
    # check if any group in a conflict-set is already in sets
    newSet = True
    for g in conflict:
      for i in range(len(conflictSets)):
        if g in conflictSets[i]:
          conflictSets[i].update(conflict)
          newSet = False
          break
      else:
        continue  # only executed if the inner loop did NOT break
      break  # only executed if the inner loop DID break

    if (newSet == True):
      conflictSets.append(conflict)

    j += 1
    gcmstoolbox.printProgress(j, k)

  if options.conflictfiles:
    conflictLists = []
    for s in conflictSets:
      conflictLists.append(list(s))
    gcmstoolbox.saveJSON(conflictLists, "conflicting_groups_stage2.json")

  # step 2: attempting to merge groups
  
  print(" - Attempting to merge groups")

  gcmstoolbox.saveJSON(stage1, "stage1.json")
  gcmstoolbox.saveJSON(stage2, "stage2.json")

  #for s in conflictSets[i]:






  
  ### UPDATE JSON FILE
  
  if options.verbose or options.veryverbose: print("\nUpdate JSON output file: " + options.jsonout + "\n")
  
  stats = groupstats(stage2)

  data["info"]["mode"] = "group"
  data["info"]["grouping"] = stats
  data["info"]["cmds"].append(cmd)
  data["groups"] = stage2

  for g in data["groups"]:
    data["groups"][g]["spectra"] = list(data["groups"][g]["spectra"])

  gcmstoolbox.saveJSON(data, options.jsonout)     # backup and save json
  print("\nFinalised. Wrote " + options.jsonout + "\n")



  ### STATISTICS
  
  print("\nSTATISTICS")
  print("  - Number of mass spectra:       " + str(len(data['spectra'])))
  print("  - Number of hitlists (stage 1): " + str(len(stage1)))

  print("  - Number of groups (stage 2):   " + str(len(stage2)))
  print("  - Number of merge conflicts:    " + str(len(conflicts)))

  print("  - Number of conflict sets:      " + str(len(conflictSets)))

  print("  - Total number of attributions: " + str(stats[0]))

  print("  - Number of hits per group:")
  print("      - [      1] " + str(stats[1]))
  print("      - [      2] " + str(stats[2]))
  print("      - [      3] " + str(stats[3]))
  print("      - [ 4 -  9] " + str(stats[4]))
  print("      - [10 - 19] " + str(stats[5]))
  print("      - [20 - 39] " + str(stats[6]))
  print("      - [40 - 59] " + str(stats[7]))
  print("      - [60 - 79] " + str(stats[8]))
  print("      - [80 - 99] " + str(stats[9]))
  print("      - [ >= 100] " + str(stats[10]) + "\n\n")

  exit()



def getRI(s, spectra):
  if s in spectra:
    if 'RI' in spectra[s]:
      return float(spectra[s]['RI'])
    else:
      return 0
  
  #if the spectrum doesn't exist: ERROR
  else:
    print("\n!! FATAL ERROR: spectrum " + s + " was not found in the GCMStoolbox JSON data file.\n")



def groupstats(groups, verbose = False):
  stats = [0] * 11  # a list of 11 zero's

  for n, group in groups.items():
    count = len(group['spectra'])
    
    # count all
    stats[0] += count

    # count in category
    if    1 <= count <=  3: stats[count] += 1
    elif  4 <= count <=  9: stats[4] += 1
    elif 10 <= count <= 19: stats[5] += 1
    elif 20 <= count <= 39: stats[6] += 1
    elif 40 <= count <= 59: stats[7] += 1
    elif 60 <= count <= 79: stats[8] += 1
    elif 80 <= count <= 99: stats[9] += 1
    elif count >= 100:      stats[10] += 1
    
  return stats


 
if __name__ == "__main__":
  main()
