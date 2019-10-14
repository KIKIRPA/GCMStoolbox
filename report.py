#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from optparse import OptionParser, OptionGroup
from collections import OrderedDict
from copy import deepcopy
import csv
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (" + gcmstoolbox.date + ") *")
  print(  "*   Licence: GNU GPL version 3.2                                              *")
  print(  "*                                                                             *")
  print(  "* REPORT                                                                      *")
  print(  "*   Generate CSV report of a component library                                *") 
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options] REPORT_CSV"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose",  help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-i", "--jsonin",  help="JSON input file name [default: gcmstoolbox.json]", action="store", dest="jsonin", type="string", default="gcmstoolbox.json")
  parser.add_option("-g", "--groupby", help="Group measurements", action="store", dest="group_by", type="string", default="sample")

  (options, args) = parser.parse_args()
  

  ### ARGUMENTS

  cmd = " ".join(sys.argv)

  if options.verbose: print("Processing arguments...")
  
 # output file
  if len(args) == 0: #exit without complaining
    print("\n!! Needs a file name for the CSV report")
    exit()
  elif len(args) == 1:
    outfile = args[0]
  else:
    print("\n!! Too many arguments")
    exit()
  
  # check and read JSON input file
  data = gcmstoolbox.openJSON(options.jsonin)
  if data['info']['mode'] != "components":
    print("\n!! Reports can only be generated if the components have been built.")
    exit()
   
  if options.verbose:
    print(" => JSON input file:  " + options.jsonin + "\n")





### READ COMPONENTS

  print("\nRunning through components...")
  
  for c in data['components']
    component = data['components'][c]

    # TODO spectrum --> groupby-categories
    intensities = OrderedDict()
    spectrumcount = 0
    for s in component['Spectra']:
      spectrum = data['spectra'][s]
      if 'Sample' in s:   intensities = spectrum['Sample']
      elif 'Source' in s: intensities = spectrum['Source']
      else:               intensities = 'Unknown'
      sumIS = 0
      if 'IS' in s: sumIS += int(spectrum['IS'])
      else :        sumIS = 1
      intensities[sample] = sumIS
      spectrumcount += 1

    # report things
    reportline = [
      "C" + component['DB#'], # column A: component number
      component['RI'],        # column B: component RI
      component['dRI'],       # column C: RI difference within the component
      spectrumcount,          # column D: number of spectra on which this group group/component was calculated
      intensities             # ordereddict with category -> sum of intensities
    ]                                                   
    report.append(reportline)
    
    
    # update progress bar
    if options.verbose:
      print("  - " + c)
    else:
      gcmstoolbox.printProgress(i, j)


  ### MAKE REPORT
  
  print("\nGenerating report...")
  
  if not options.verbose: 
    i = 0
    j = len(report)
    gcmstoolbox.printProgress(i, j)
  
  # compile a list of all group-by categories
  categories = set()
  for line in report:
    categories.update(line[4].keys())
  
  # write report file
  with open(outfile, 'w', newline='') as fh:
    mkreport = csv.writer(fh, dialect='excel')

    # header
    mkreport.writerow(["component", "RI", "dRI", "number of spectra"] + sorted(categories))
    
    # rows with total integrated signals and total number of spectra for each of the groupby categories 
    # TODO spectrum --> groupby-categories
    intensities = OrderedDict()
    spectrumcount = OrderedDict()
    for category in sorted(categories): 
      intensities[category] = 0
      spectrumcount[category] = 0
    for s in data['spectra'].values():
      if 'Sample' in s:   spCategory = s['Sample']
      elif 'Source' in s: spCategory = s['Source']
      else:               spCategory = 'Unknown'
      if spCategory in categories:
        if 'IS' in s: 
          intensities[spCategory] += int(s['IS'])
          spectrumcount[spCategory] += 1
    mkreport.writerow(["total IS", "", "", "", ""] + list(intensities.values()))
    mkreport.writerow(["number of spectra", "", "", "", ""] + list(spectrumcount.values()))
    
    # next rows: components
    for line in report:
      intensities = line.pop()
      for category in sorted(categories):
        if category in intensities.keys(): line.append(intensities[category])
        else:                   line.append("")
      mkreport.writerow(line)
      
      if not options.verbose: 
        i += 1
        j = len(report)
        gcmstoolbox.printProgress(i, j)
      
  print(" => Wrote " + outfile)
  exit()
  
    
if __name__ == "__main__":
  main()
