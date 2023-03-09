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
  group.add_option("-t", "--tolerance", help="Allow an RI spread tolerance factor after merging groups [default: 1.5]",  action="store", dest="tolerance", type="float", default=1.5)
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


  ### STEP 1: GENERATE LIST OF HITS PER UNKNOWN
 
  # init progress bar
  print("\nStep1: Generate lists of hits per unknown")
  print("Processing " + inFile)
  j = 0
  k = len(data['spectra'])
  if not (options.verbose or options.veryverbose) :
    gcmstoolbox.printProgress(j, k)

  # read MSPEPSEARCH file line by line, and apply grouping criteria
  hits = []
  step1 = dict()
  with open(inFile,'r') as fh:
    for line in fh:

      if line.casefold().startswith('unknown'):
        # PROCESS PREVIOUS
        if len(hits) > 0:
          step1[unknown] = hits

          # report stuff
          if options.veryverbose:
            print(f' - "{unknown}": {len(hits)} retained hits, {i-len(hits)} rejected hits:')
            print(f'    - RI window: {round(unknownRI - window, 1)} <= RI <= {round(unknownRI + window, 1)}')
            for hit in hits:
              print('    - retained hit: {}'.format(hit))
          elif options.verbose:
            print(f' - "{unknown.split()[0]}": {len(hits)} retained hits, {i-len(hits)} rejected hits')
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
 

  ### STEP 2: FIRST GROUPING

  # init progress bar
  print("\n\n\nStep 2: First grouping - attributing hitlists to interim groups")
  j = 0
  step1_count = len(step1)
  if not (options.verbose or options.veryverbose) :
    gcmstoolbox.printProgress(j, step1_count)

  step2 = dict()

  # loop over unkowns
  for unknown in step1:
    j += 1
    attributed_groups = set()

    # loop over hits for this unknown
    for hit in step1[unknown]:
      if hit in step2:
        attributed_groups.update(step2[hit])
    
    # if none of the hits have been attributed to a group, add it to a new group
    if len(attributed_groups) == 0:
      attributed_groups.add(j)

    # attribute all hits to the group(s)
    for hit in step1[unknown]:
      step2[hit] = list(attributed_groups)

    # report stuff
    if options.verbose or options.veryverbose:
      print(f' - "{unknown.split()[0]}": spectra attributed to intermediary groups {str(attributed_groups)}')
    else: 
      gcmstoolbox.printProgress(j, step1_count)


  ### STEP 3: SECOND GROUPING

  # init progress bar
  print("\n\nStep 3: Second grouping - merge cross-referenced groups")
  j = 0
  step2_count = len(step2)
  if not (options.verbose or options.veryverbose) :
    gcmstoolbox.printProgress(j, step2_count)

  step3 = dict()

  # reverse order of step2 dict
  step2 =dict(reversed(list(step2.items())))

  # loop over spectra
  while len(step2) > 0:
    j += 1

    (spectrum, groups) = step2.popitem()

    # add spectrum to the asigned group
    primary_group_id = groups[0]
    if primary_group_id not in step3:
      step3[primary_group_id] = dict()
      step3[primary_group_id]["spectra"] = list()
    step3[primary_group_id]["spectra"].append(spectrum)

    if options.verbose or options.veryverbose:
      print(f' - "{spectrum.split()[0]}": spectra attributed to cross-referenced group {str(primary_group_id)}')
    
    # replace all alternative group ids with the primary group id in all remaining elements of step2
    if len(groups) > 1:
      remove_group_ids = groups[1:]
      for remaining_item in step2:
        remaining_item_groups = step2[remaining_item]
        # replace each alternative group id with the primary in this item of step2
        for alt_group_id in remove_group_ids:
          if alt_group_id in remaining_item_groups:
            remaining_item_groups = [primary_group_id if x==alt_group_id else x for x in remaining_item_groups]
            if options.veryverbose:
              print(f'   - removing {str(alt_group_id)} from intermediairy group {str(remaining_item)}')
        # store updated group list back in step2
        step2[remaining_item] = list(set(remaining_item_groups))

    # report progress
    if not options.verbose and not options.veryverbose: 
      gcmstoolbox.printProgress(j, step2_count)


  ### STEP 4: GROUP EVALUATION

  # init progress bar
  print("\n\nStep 4: Group evaluation - split groups with large RI range")

  # check tolerance factor
  if options.tolerance < 1 and (options.rifixed != 0 or options.rifactor != 0):
    options.tolerance = 1
    print("!! tolerance factor too low, now set at 1")

  i = 0 # final group numbers
  j = 0
  step3_count = len(step3)

  if not (options.verbose or options.veryverbose) :
    gcmstoolbox.printProgress(j, step3_count)

  step4 = dict()

  # reverse order of step3 dict
  step3 = dict(reversed(list(step3.items())))

  # loop over cross-referenced groups
  while len(step3) > 0:
    j += 1
    ri_list = []
    groups_to_add = []

    (group_id, group_details) = step3.popitem()

    # get list of RIs from the group
    for spectrum in group_details["spectra"]:
      ri = getRI(spectrum, data['spectra']) if (window != 0) else 0
      if (ri != 0):
        ri_list.append(ri)
    
    # only evaluate groups when all spectra in the group have an RI
    count = len(group_details["spectra"])
    group_details["count"] = count
    if count == len(ri_list):
      ri_mean = round(mean(ri_list), 1)
      ri_min = round(min(ri_list), 1)
      ri_max = round(max(ri_list), 1)
      ri_delta = abs(ri_max - ri_min)
      group_details["meanRI"] = ri_mean
      group_details["minRI"] = ri_min
      group_details["maxRI"] = ri_max
      group_details["deltaRI"] = ri_delta

      if (options.rifixed != 0) or (options.rifactor != 0):
        ri_tolerance = abs((options.rifixed + (options.rifactor * ri_mean)) * options.tolerance)

        # check if RI spread is greater than the tolerance
        if ri_delta < ri_tolerance:
          group_details["deltaRI_tolerance"] = ri_tolerance

        else: # split group into multiple parts
          number_of_groups = (ri_delta // ri_tolerance) + 1   # "//"" is floor (integer) division operator
          number_of_groups= int(number_of_groups)
          divider = ri_delta / number_of_groups

          for n in range(number_of_groups):
            new_group = dict()
            new_group["spectra"] = []
            ri_list = []

            # calculate min and max RI's for this new group, used for splitting
            # when comparing ri to min and max in each new group, we must add a very small number to the max
            # otherwise we risk loosing the spectrum with the highest RI in the original group
            new_group_min = ri_min + n * divider
            new_group_max = ri_min + (n + 1) * divider + 0.01

            # collect the spectra for the new group
            for spectrum in group_details["spectra"]:
              ri = getRI(spectrum, data['spectra'])
              if ri >= new_group_min and ri < new_group_max:
                new_group["spectra"].append(spectrum)
                ri_list.append(ri)

            # add statistics for the new group
            new_group["count"] = len(new_group["spectra"])
            new_group["meanRI"] = round(mean(ri_list), 1)
            new_group["minRI"] = round(min(ri_list), 1)
            new_group["maxRI"] = round(max(ri_list), 1)
            new_group["deltaRI"] = abs(ri_max - ri_min)
            new_group["deltaRI_tolerance"] = ri_tolerance = abs((options.rifixed + (options.rifactor * ri_mean)) * options.tolerance)

            groups_to_add.append(new_group)
        
      # if we haven't split the group (no RI-checking, missing RIs or not split)
      if len(groups_to_add) == 0:
        i += 1
        step4[f"G{str(i)}"] = group_details
        if options.verbose or options.veryverbose:
          print(f' - "G{str(i)}": based on cross-referenced group {str(group_id)} (RI delta: {str(group_details["deltaRI"])}, RI tolerance: {str(group_details["deltaRI_tolerance"])})')
      else:
        if options.verbose or options.veryverbose:
            print(f' - SPLIT cross-referenced group {str(group_id)} (RI delta: {str(group_details["deltaRI"])}, RI tolerance: {str(group_details["deltaRI_tolerance"])})')
        for g in groups_to_add:
          i += 1
          step4[f"G{str(i)}"] = g
          if options.veryverbose:
            print(f'   - "G{str(i)}": based on cross-referenced group {str(group_id)} (RI delta: {str(g["deltaRI"])}, RI tolerance: {str(g["deltaRI_tolerance"])}')

    # report progress
    if not options.verbose and not options.veryverbose: 
      gcmstoolbox.printProgress(j, step3_count)


  ### UPDATE JSON FILE
  
  if options.verbose or options.veryverbose: 
    print("\nUpdate JSON output file: " + options.jsonout + "\n")
  
  stats = groupstats(step4)

  data["info"]["mode"] = "group"
  data["info"]["grouping"] = stats
  data["info"]["cmds"].append(cmd)
  data["groups"] = step4

  for g in data["groups"]:
    data["groups"][g]["spectra"] = list(data["groups"][g]["spectra"])

  gcmstoolbox.saveJSON(data, options.jsonout)     # backup and save json
  print("\nFinalised. Wrote " + options.jsonout)


  ### STATISTICS
  
  print("\nSTATISTICS")
  print(" - Number of mass spectra:                            " + str(len(data['spectra'])))
  print(" - Number of hitlists (step 1):                       " + str(step1_count))
  print(" - Number of intermediary groups (step 2):            " + str(step2_count))
  print(" - Number of cross-referenced groups (step 3):        " + str(step3_count))
  print(" - Number of groups after RI tolerance check (step4): " + str(len(step4)))
  print("")
  print(" - Total number of attributions:                      " + str(stats[0]))
  print("")
  print(" - Number of hits per group:")
  print("      [      1]  ->  " + str(stats[1]) + " groups")
  print("      [      2]  ->  " + str(stats[2]) + " groups")
  print("      [      3]  ->  " + str(stats[3]) + " groups")
  print("      [ 4 -  9]  ->  " + str(stats[4]) + " groups")
  print("      [10 - 19]  ->  " + str(stats[5]) + " groups")
  print("      [20 - 39]  ->  " + str(stats[6]) + " groups")
  print("      [40 - 59]  ->  " + str(stats[7]) + " groups")
  print("      [60 - 79]  ->  " + str(stats[8]) + " groups")
  print("      [80 - 99]  ->  " + str(stats[9]) + " groups")
  print("      [ >= 100]  ->  " + str(stats[10]) + " groups\n\n")

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



def groupstats(groups):
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
