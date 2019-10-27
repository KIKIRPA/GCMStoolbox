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
  print(  "*   Version: {} ({})                                             *".format(gcmstoolbox.version, gcmstoolbox.date))
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *")
  print(  "*   Licence: GNU GPL version 3                                                *")
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
  parser.add_option("-o", "--jsonout", help="JSON output file name [default: same as JSON input file]", action="store", dest="jsonout", type="string")
  parser.add_option("-g", "--groupby", help="Group measurements by categories (eg. Source, Sample, AAdays, Resin...)", action="store", dest="groupby", type="string", default="Source")

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

  # json output 
  if options.jsonout == None: 
    options.jsonout = options.jsonin

  if options.verbose:
    print(" => JSON input file:  " + options.jsonin)
    print(" => JSON output file: " + options.jsonout)
    print(" => Output msp file:  " + mspfile + "\n")


  ### READ COMPONENTS

  print("\nRunning through components...")
  report = []

  if not options.verbose: 
    i = 0
    j = len(data['components'])
    gcmstoolbox.printProgress(i, j)
  
  for c in data['components']:
    component = data['components'][c]

    # check all spectra of a component and search for the group-by categories
    for s in component['Spectra']: 
      spectrum = data['spectra'][s]
      categories = OrderedDict()

      # lookup category in spectrum (or default to unknown)
      if options.groupby in spectrum:
        cat = spectrum[options.groupby]
      else:
        cat = 'unknown'

      # spectrumIS
      if 'IS' in spectrum: spectrumIS = int(spectrum['IS'])
      else:                spectrumIS = 1

      # store IS and count in categories
      if cat not in categories:
        categories[cat] = OrderedDict(
          [('sumIS', spectrumIS), ('count', 1)]
        )
      else:
        categories[cat]['sumIS'] += spectrumIS
        categories[cat]['count'] += 1

    # divide sumIS by the number of spectra
    for cat in categories:
      meanIS = categories[cat]['sumIS'] // categories[cat]['count'] #integer division!
      categories[cat] = meanIS  # this is what we need to report, sumIS and count can thus be overwritten

    # prepare report line for this component
    reportline = [
      "C" + component['DB#'],     # column A: component number
      len(component['Spectra']),  # column B: number of spectra on which this group group/component was calculated
      component['RI'],            # column C: component RI
      component['dRI'],           # column D: RI difference within the component
      categories                  # ordereddict with category -> mean intensities
    ]                                                   
    report.append(reportline)    
    
    # update progress bar
    if options.verbose:
      print("  - " + c)
    else:
      i += 1
      gcmstoolbox.printProgress(i, j)



  ### CALCULATE SUM-IS 
  
  # the sum-IS is the sum of all spectra of a given source file
  # in case a category is composed of multiple source files, the sum-IS is a the average
  # (sum of the IS values of all spectra within this category, divided by the number of sources)

  print("\nCalculate IS for each " + options.groupby + "...")

  if not options.verbose: 
    i = 0
    j = len(data['spectra'])
    gcmstoolbox.printProgress(i, j)

  # compile a list of all group-by categories
  categories = set()
  for line in report:
    categories.update(line[4].keys())
  categories = sorted(categories) #convert to sorted list

  # calculate sumIS and count for each category
  catIS = dict()
  catSpectra = dict()
  catSources = dict()

  for spectrum in data['spectra'].values():
    if options.groupby in spectrum:
      cat = spectrum[options.groupby]
    else:
      cat = 'unknown'

    # spectrumIS
    if 'IS' in spectrum: spectrumIS = int(spectrum['IS'])
    else:                spectrumIS = 1

    # store IS and count in categories
    if cat not in catIS:
      catIS[cat] = spectrumIS
      catSpectra[cat] = 1
      catSources[cat] = set()
    else:
      catIS[cat] += spectrumIS
      catSpectra[cat] += 1
    catSources[cat].add(spectrum['Source'])

    # update progress bar
    if options.verbose:
      print("  - S{}: category {} (#{})--> added {} to summed IS".format(spectrum['DB#'], cat, catSpectra[cat], spectrumIS))
    else:
      i += 1
      gcmstoolbox.printProgress(i, j)

  # calculate mean IS
  for cat in categories:
    # count sources per category
    catSources[cat] = len(catSources[cat])
    # calculate average sum-IS
    catIS[cat] = catIS[cat] // catSources[cat]



  ### MAKE REPORT
  
  print("\nGenerating report...")
  
  if not options.verbose: 
    i = 0
    j = len(report)
    gcmstoolbox.printProgress(i, j)
    
  # write report file
  with open(outfile, 'w', newline='') as fh:
    mkreport = csv.writer(fh, dialect='excel')

    # write header rows
    mkreport.writerow(["component",           "number of spectra", "RI", "dRI"] + categories)
    mkreport.writerow(["(average sum-IS)",    "",                  "",   ""   ] + [catIS[cat]      for cat in categories])
    mkreport.writerow(["(number of spectra)", "",                  "",   ""   ] + [catSpectra[cat] for cat in categories])
    mkreport.writerow(["(number of sources)", "",                  "",   ""   ] + [catSources[cat] for cat in categories])
    
    # next rows: components
    for row in report:
      # the last item in a report item (row) is a dict of categories and mean IS
      # replace it with a complete and sorted list of mean IS'es
      catIS = row.pop()
      for cat in categories:
        if cat in catIS: row.append(catIS[cat])
        else:            row.append("")
      # write row to report
      mkreport.writerow(row)
      
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
      
  print("\n => Wrote {}\n".format(outfile))

  ### TRACE IN JSON FILE
  
  print("\nPut a trace in the JSON output file: " + options.jsonout + "\n")
  data = gcmstoolbox.openJSON(options.jsonin)     # reread the file to be sure we haven't accidentally messed up the data
  data['info']['cmds'].append(" ".join(sys.argv)) # put a trace in the data file
  gcmstoolbox.saveJSON(data, options.jsonout)     # backup and safe json

  exit()
  
    
if __name__ == "__main__":
  main()
