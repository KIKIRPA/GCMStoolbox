#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from collections import OrderedDict
from glob import glob
from optparse import OptionParser, OptionGroup
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Version: {} ({})                                             *".format(gcmstoolbox.version, gcmstoolbox.date))
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *")
  print(  "*   Licence: GNU GPL version 3                                                *")
  print(  "*                                                                             *")
  print(  "* EXPORT:                                                                     *")
  print(  "*   export the GCMStoolbox data file (JSON) into NIST MS SEARCH format (.msp) *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")


  ### OPTIONPARSER
  
  usage = "usage: %prog [options] MSP_FILE"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose", help="Be very verbose [not default]", action="store_true", dest="verbose", default=False)
  parser.add_option("-i", "--jsonin",  help="JSON input file name [default: gcmstoolbox.json]", action="store", dest="jsonin", type="string", default="gcmstoolbox.json")
  parser.add_option("-o", "--jsonout", help="JSON output file name [default: same as JSON input file]", action="store", dest="jsonout", type="string")
  parser.add_option("-m", "--mode",    help="Mode: auto|spectra|group|components [default:auto]", action="store", dest="mode", type="string", default="auto")
  parser.add_option("-g", "--group",   help="Group numbers to export in group mode; multiple instances can be defined", action="append", dest="group", type="string")
  
  (options, args) = parser.parse_args()

  ### ARGUMENTS AND OPTIONS
  
  cmd = " ".join(sys.argv)
  
  if options.verbose: print("Processing import files and options")

  # check MSP output file
  if len(args) == 0:
    print("  !! No MSP file name given\n")
    exit()
  elif len(args) != 1:
    print("  !! Too many arguments. Only one MSP file name can be created.\n")
    exit()
  else:
    mspfile = args[0]

  # check and read JSON input file
  data = gcmstoolbox.openJSON(options.jsonin)
    
  # json output 
  if options.jsonout == None: 
    options.jsonout = options.jsonin

  if options.verbose:
    print(" => JSON input file:  " + options.jsonin)
    print(" => JSON output file: " + options.jsonout)
    print(" => Output msp file:  " + mspfile + "\n")


  ### MODE
  
  if options.mode.lower().startswith('a'):
    mode = data['info']['mode']
    if mode == 'filter': mode = 'group'
  elif options.mode.lower().startswith('s'):
    mode = 'spectra'
  elif options.mode.lower().startswith('g'):   
    mode = 'group'
    if data['info']['mode'] == 'spectra':
      print("  !! No groups defined - run groups.py first\n")
      exit()
    if len(options.group) == 0:
      print("  !! Group mode requires at least one group (-g)\n")
      exit()
  elif options.mode.lower().startswith('c'):
    mode = 'components'
    if data['info']['mode'] != 'components':
      print("  !! No components defined - run componentlib.py first\n")
      exit()
  else:
    print("  !! Unknown mode (possible modes are 'auto', 'spectra', 'group' and 'components'\n")
    exit()
  
  print("Mode: " + mode)
    
    
  ### WRITE FILE
  
  print("\nProcessing mass spectra")
  
  # make list of spectra to be added
  splist = OrderedDict()
  if (mode == "spectra") or (mode == "components"):
    splist = data[mode]
  elif mode == "group":
    for g in options.group:
      if 'G' + str(g) in data['groups']:
        # add original spectra to splist
        for s in data['groups']['G' + str(g)]['spectra']:
          splist[s] = data['spectra'][s]
        # if a component exists with a sumspectrum, add this.
        if 'component' in data['groups']['G' + str(g)]:
          c = data['groups']['G' + str(g)]['component']
          splist[c] = data['components'][c]
      else:
        print(" !! G" + str(g) + " was not found.")
  
  
  with open(mspfile, "w") as fh:
    # init progress bar
    if not options.verbose: 
      j = 0
      k = len(splist)
      gcmstoolbox.printProgress(j, k)
    
    for name, spectrum in splist.items():
      writespectrum(fh, mspfile, name, spectrum, options.verbose)
    
      # adjust progress bar
      if not options.verbose: 
        j += 1
        gcmstoolbox.printProgress(j, k)

  
  print("\nFinalised. Wrote " + mspfile + "\n")  

  
  ### TRACE IN JSON FILE
  
  if options.verbose: print("Put a trace in the JSON output file: " + options.jsonout + "\n")
  data = gcmstoolbox.openJSON(options.jsonin)     # reread the file to be sure we haven't accidentally messed up the data
  data['info']['cmds'].append(" ".join(sys.argv)) # put a trace in the data file
  gcmstoolbox.saveJSON(data, options.jsonout)     # backup and safe json
   
  exit()
    
  
  
  
def writespectrum(fh, fn, name, sp, verbose = False):
  # write the spectrum to the file handle line by line in NIST MSP format
  # don't mind to much about the order of the lines; we start with Name, and end with NumPeaks and the spectral data

  # build comments, while removing fields that don't belong in the msp
  comments = ""
  list = ['Sample', 'Resin', 'AAdays', 'Color', 'PyTemp', 'OR', 'IS', 'RA', 'SN', 'dRI']
  for l in list:
    val = sp.pop(l, False)
    if val:
      comments += l + "=" + val.replace(" ", "_") + " "
  if "RI" in sp:
    comments += "RI=" + sp['RI'] + " "
  if "RT" in sp:
    comments += "RT=" + sp['RT']
  
  # remove other fields
  numpeaks = sp.pop('Num Peaks')
  xydata   = sp.pop('xydata')
  compospectra = sp.pop('Spectra', None)
  composamples = sp.pop('Samples', None)
  
  #if compospectra:   commented out: too long comments seem to prevent AMDIS to use RI
  #  comments += " " + " | ".join([cs.replace("=", "").replace(" ","_") for cs in compospectra])
  
  #verbose
  if verbose:
    print("    - Write", name, "in output file")
  
  #start with the Name field (and remove it from the dictionary)
  fh.write('Name: '   + name + "\n")
  
  # make sure we 'll have a CAS number 
  if 'CAS#' not in sp:
    casno = os.path.basename(fn)
    casno = os.path.splitext(casno)[0]
    casno += "-" + name.split(" ", 1)[0]
    fh.write('CAS#: ' + casno + "\n")
  
  #then iterate over the remaining items
  for key, value in sp.items():
    fh.write(key + ': ' + value + "\n")
    
  # make sure we'll have a source
  if 'SOURCE' not in sp:
    fh.write('SOURCE: ' + fn + "\n")
  
  # write comments
  fh.write('Comments: ' + comments.strip() + "\n")
  
  # write NumPeaks
  fh.write('Num Peaks: ' + str(numpeaks) + "\n")
  
  # NIST MSP usually puts 5 couples on each line (although this is no requirement)
  # 1. iterate over full lines
  div = numpeaks // 5          # we have %div full lines
  for i in range(div):         
    line = ""  
    for j in range(5): 
      x, y = xydata.popitem(last = False)
      line = line + str(x) + " " + str(y) + "; "
    fh.write(line.rstrip(" ") + "\n")
  # 2. iterate over the last incomplete line
  mod = numpeaks % 5           # the last line will have mod couples
  if mod > 0:
    line = ""
    for i in range(mod):
      x, y = xydata.popitem(last = False)
      line = line + str(x) + " " + str(y) + "; "
    fh.write(line.rstrip(" ") + "\n")
  fh.write("\n")



if __name__ == "__main__":
  main()
