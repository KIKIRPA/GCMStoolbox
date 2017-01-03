#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from glob import glob
from optparse import OptionParser, OptionGroup
import json
import csv
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (3 Jan 2017)  *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* COMPONENTLIB                                                                *")
  print(  "*   Makes a NIST msp file with components as defined in the groups json file  *") 
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options] SOURCE_MSP_FILE GROUP_JSON_FILE"
  parser = OptionParser(usage, version="%prog 1.0")
  parser.add_option("-v", "--verbose",  help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-c", "--cnumber",  help="Start number for component numbers", action="store", dest="c", type="int" , default=1)
  parser.add_option("-p", "--preserve", help="Preserve group numbers", action="store_true", dest="preserve", default=False)
  parser.add_option("-e", "--elinc",    help="Special formatting for ELinC data", action="store_true", dest="elinc", default=False)
  parser.add_option("-o", "--outfile",  help="Output file name [default: componentlib.msp]", action="store", dest="outfile", type="string", default="componentlib.msp")
  (options, args) = parser.parse_args()

  ### ARGUMENTS

  if options.verbose: print("Processing arguments...")

  # preserve and c number flags cannot be used together
  if options.preserve and (options.c != 1):
    print("\n!! The options -c (--cnumber) and -p (--preserve) cannot be used together.")
    exit()

  # input file
  if len(args) == 0: #exit without complaining
      exit()
  elif len(args) != 2:
    print("\n!! This program should have two arguments: firstly the SOURCE_MSP_FILE and secondly the GROUP_JSON_FILE")
    exit()
  else:
    if os.path.isfile(args[0]):
      sourceFile = args[0]
    else:
      print("\n!! SOURCE_MSP_FILE '" + args[0] + "' not found.")
      exit()
      
    if os.path.isfile(args[1]):
      with open(args[1],'r') as fh:    
        groups = json.load(fh)
    else:
      print("\n!! GROUP_JSON_FILE '" + args[1] + "' not found.")
      exit()  
  
  
  ### READ SPECTRA
  
  # make a list of spectra that need to be fetched
  splist = []
  for group in groups.values():
    splist.extend(group['spectra'])
  
  # stdOut
  print("\nRead the required data from " + sourceFile)
  if not options.verbose: 
    i = 0
    j = len(splist)
    gcmstoolbox.printProgress(i, j)

  # read spectra from msp file
  spectra = {}
  with open(sourceFile,'r') as fh:
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


  ### MAKE SUM SPECTRA
  
  # stdOut
  print("\nBuilding component library")
  
  i = 0  # we'll use this both for the progress bar and for the component number (i + options.c, if options.preserve is false)
  report = []
  
  if not options.verbose: 
    j = len(groups.keys())
    gcmstoolbox.printProgress(i, j)
  
  with open(options.outfile,'w') as fh:
    for g in sorted(int(x) for x in groups.keys()):
      # init
      groupspectra = []
      name = []            # for sum spectrum
      comments = []        # for sum spectrum
      csvSpectra = []      # for cvs report
      csvMeasurements = [] # for cvs report
      
      # group or component numbering:
      if not options.preserve: c = i + options.c
      else:                    c = g
      
      # collect the spectra
      for s in groups[str(g)]['spectra']:
        if not options.elinc: csvSpectra.append(s)
        groupspectra.append(spectra.pop(s))
      
      # if more than one spectrum, make sumspectrum
      if len(groupspectra) > 1:
        sp = gcmstoolbox.sumspectrum(*groupspectra, name="")
      else:
        sp = groupspectra[0]
          
      # rebuild the spectra metadata (and change for single spectra things)
      for s in groupspectra:
        name.append(s['Name'])
        comments.append(s['Comments'])
        if not options.elinc: csvMeasurements.append(s['Source'])
      
      if options.elinc:
        csvSpectra, csvMeasurements = elincize(sp, "C" + str(c), name, comments)
      else:
        sp['Name'] = "C" + str(c) + " [ " + " | ".join(name) + " ] " + sp['Name']
        sp['Comments'] = "RI=" + str(sp['RI']) + " " + " | ".join(comments)
        
      # report things
      reportline = ["C" + str(c), "G" + str(g), " ".join(csvSpectra), csvMeasurements]
      report.append(reportline)
      
      # write spectrum
      gcmstoolbox.writespectrum(fh, sp, options.verbose)
      
      # progress bar
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
        
  print("  --> Wrote " + options.outfile)
  
        
  ### MAKE SUM SPECTRA
  
  print("\nGenerating report")
  
  # compile a list of all measurements
  allmeas = set()
  for line in report:
    allmeas.update(line[3])
  
  # build the measurement grid
  for line in report:
    match = line.pop()
    for m in sorted(allmeas):
      if m in match: line.append("Y")
      else:          line.append(" ")
  
  # write report file
  with open(options.outfile + '.csv', 'w', newline='') as fh:
    mkreport = csv.writer(fh, dialect='excel')
    mkreport.writerow(["component", "group", "spectra"] + sorted(allmeas))
    for line in report:
      mkreport.writerow(line)
      
  print("  --> Wrote " + options.outfile + ".csv\n")






def elincize(sp, prefix, names, comments, verbose = False):
  # special formatting for ELinC data
  # 1. short sample names
  
  short = { "BLK0000": "BLA",
            "BLK0002": "LAR",
            "BLK0004": "MAN",
            "BLK0005": "PIC",
            "BLK0007": "SEE",
            "BLK0008": "COL",
            "BLK0009": "ABI",
            "BLK0012": "MAS",
            "BLK0013": "GAM",
            "BLK0014": "ELE",
            "BLK0017": "KAU",
            "BLK0026": "COP",
            "BLK0031": "STI",
            "BLK0032": "SUM",
            "BLK0040": "TUN",
            "BLK0045": "EAF",
            "BLK0048": "SA2",
            "BLK0065": "HCN",
            "BLK0066": "HCF",
            "BLK0067": "CON",
            "BLK0070": "MAD"
          }
  
  # 2. split the spectrum names in reusable lists
  specno = []
  meas = []
  samples = set()
  aging = set()
  color = set()
  temp = set()
  
  for name in names:
    parts = name.split(' ')
    specno.append(parts[0])
    meas.append(parts[2])
    
    parts = parts[2].split('-')
    samples.add(parts[0])
    aging.add(parts[2][:-1])
    color.add(parts[2][-1:])
    temp.add(parts[3])
  
  samples2 = set()
  for x in samples:
    if x in short.keys():
      samples2.add(short[x])
    else:
      samples2.add(x)

  # 3. update spectrum sp
  sp['Name'] = ( prefix + " " + 
                 "-".join(sorted(samples2)) + 
                 " D=" + "-".join(sorted(aging)) + 
                 " C=" + "-".join(sorted(color)) +
                 " T=" + "-".join(sorted(temp)) +
                 " RI=" + sp['RI']
               )
  sp['Comments'] += " " + " | ".join(names).replace("=", "")
  
  # 4. update names and spectra for cvs report
  meas = list(set(meas)) #remove duplicates
  return sorted(specno), sorted(meas)
  


    
if __name__ == "__main__":
  main()
