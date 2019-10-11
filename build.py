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
  print(  "* BUILD                                                                       *")
  print(  "*   Builds the component spectra                                              *") 
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options]"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose",  help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-i", "--jsonin",  help="JSON input file name [default: gcmstoolbox.json]", action="store", dest="jsonin", type="string", default="gcmstoolbox.json")
  parser.add_option("-o", "--jsonout", help="JSON output file name [default: same as JSON input file]", action="store", dest="jsonout", type="string")
  parser.add_option("-c", "--cnumber",  help="Start number for component numbers", action="store", dest="c", type="int" , default=1)
  parser.add_option("-p", "--preserve", help="Preserve group numbers", action="store_true", dest="preserve", default=False)
  parser.add_option("-s", "--sum",      help="Calculate sumspectra with the N spectra with highest signal, 0 for all [default: 0]", action="store",  dest="n", type="int", default=0)

  (options, args) = parser.parse_args()
  

  ### ARGUMENTS

  cmd = " ".join(sys.argv)

  if options.verbose: print("Processing arguments...")
  
  # check number of arguments
  if len(args) != 0: #exit without complaining
    print("\n!! Too many arguments")
    exit()
  
  # check and read JSON input file
  data = gcmstoolbox.openJSON(options.jsonin)
  if data['info']['mode'] == 'spectra':
    print("\n!! Cannot build components using ungrouped spectra.")
    exit()
  
  # json output 
  if options.jsonout == None: 
    options.jsonout = options.jsonin

  if options.verbose:
    print(" => JSON input file:  " + options.jsonin)
    print(" => JSON output file: " + options.jsonout + "\n")

  # preserve and c number flags cannot be used together
  if options.preserve and (options.c != 1):
    print("\n!! The options -c (--cnumber) and -p (--preserve) cannot be used together.")
    exit()


  ### APPLY ACTIVE FILTERS
  
  print("\nApply filters...")
  if not options.verbose: 
    i = 0
    j = len(data['filters'])
    gcmstoolbox.printProgress(i, j)
  
  out = set()
  for id, f in data['filters'].items():
    if f['active']:
      out.update(f['out'])
      if options.verbose: print(" - add " + id)
    if not options.verbose: 
      i += 1
      gcmstoolbox.printProgress(i, j)


  ### BUILD COMPONENTS

  print("\nBuild components...")
  
  i = 0  # we'll use this both for the progress bar and for the component number (i + options.c, if options.preserve is false)
  #report = []
  data['components'] = OrderedDict()
  
  # to sort components on RI, we'll make an intermediary groups dict (ri: groupname)
  groups = []
  ris = []
  for gid, group in data['groups'].items():
    if gid not in out: #apply filters
      if 'minRI' in group:
        # find position
        gri = float(group['minRI'])
        pos = 0
        for r in ris:
          if r <= gri:
            pos += 1 
          else: 
            break
        
        # add to groups and ris
        groups.insert(pos, gid)
        ris.insert(pos, gri)
      else: #group without minRI: add to the back of the groups list
        groups.append(gid)

  # init progress bar
  if not options.verbose: 
    j = len(groups)
    gcmstoolbox.printProgress(i, j)

  # build components from the groups
  for g in groups:
    # init
    group = data['groups'][g]
    groupspectra = []
    
    # group or component numbering:
    if not options.preserve: c = i + options.c
    else:                    c = int(g.replace('G', ''))
  
    # collect the spectra
    for s in group['spectra']:
      #if not options.elinc: csvSpectra.append(s)
      groupspectra.append(data['spectra'][s])
  
    # if more than one spectrum, make sumspectrum
    if len(groupspectra) > 1:
      sp = gcmstoolbox.sumspectrum(*groupspectra, highest=options.n)
    else:
      sp = deepcopy(groupspectra[0])
      
    # rebuild the spectra metadata (and change for single spectra things)
    name = "C" + str(c) + " RI" + str(round(float(sp['RI'])))
    sp['DB#'] = str(c)
    
    samples = OrderedDict()
    for s in groupspectra:
      if 'Sample' in s:   sample = s['Sample']
      elif 'Source' in s: sample = s['Source']
      else:               sample = 'Unknown'
      signal = 0
      if 'IS' in s: signal += int(s['IS'])
      else :        signal = 1
      samples[sample] = signal
      
    sp['Spectra'] = group['spectra']
    sp['Samples'] = list(samples.keys())
    
    for item in ["Resin", "AAdays", "Color", "PyTemp"]:
      value = set()
      for s in groupspectra:
        if item in s:
          value.add(s[item])
      if len(value) > 0:
        if item == "AAdays":
          valueint = [ int(x) for x in value ]
          valueint = sorted(valueint)
          value = [ str(x) for x in valueint ]
          # condense the list of AAdays into sequences (0,2,4,8,32 becomes 0-8,32)
          seq = []
          days = [0, 2, 4, 8, 16, 32, 64]
          k = 0
          for low in days:
            if low in valueint:        #lower limit of sequence
              seq.insert(k, str(low))
              valueint.remove(low)
              found = False
              for high in days:   
                if high > low:
                  if high in valueint: #higher limit of sequence
                    found = high
                    valueint.remove(high)
                  else:
                    break
              if found: seq[k] += "-" + str(found)
              k += 1
          # add possible AAdays values other than 0,2,4,8...
          for x in valueint: seq.append(str(x))
          sp["AAdays"] = ",".join(seq)
          name += " " + sp['AAdays'] + "d"
        elif item == "Color":
          sp['Color'] = "/".join(value)
          name += " " + sp['Color']
        else:
          sp[item] = "-".join(sorted(value))
          name += " " + sp[item]
    
    # add to data
    data['components'][name] = sp
    
    # add a "link" to the group data
    # (used to include sumspectrum if a group library is exported) 
    data['groups'][g]['component'] = name
    
    """
    # report things
    reportline = ["C" + str(c), g, " ".join(s.split(" ")[0] for s in sp['Spectra']), sp['RI'], samples]
    report.append(reportline)
    """

    i += 1
    
    # update progress bar
    if options.verbose:
      print("  - " + name)
    else:
      gcmstoolbox.printProgress(i, j)


  ### MAKE REPORT
  
  """ 
  print("\nGenerating report...")
  
  if not options.verbose: 
    i = 0
    j = len(report)
    gcmstoolbox.printProgress(i, j)
  
  # compile a list of all measurements
  allmeas = set()
  for line in report:
    allmeas.update(line[4].keys())
  
  # write report file
  with open(outfile, 'w', newline='') as fh:
    mkreport = csv.writer(fh, dialect='excel')
    mkreport.writerow(["component", "group", "spectra", "RI"] + sorted(allmeas))
    
    # calculate total integrated signals
    totIS = OrderedDict()
    for m in sorted(allmeas): totIS[m] = 0
    for s in data['spectra'].values():
      if 'Sample' in s:   m = s['Sample']
      elif 'Source' in s: m = s['Source']
      else:               m = 'Unknown'
      if m in allmeas:
        if 'IS' in s: 
          totIS[m] += int(s['IS'])
    mkreport.writerow(["total IS", "", "", ""] + list(totIS.values()))
    
    for line in report:
      samples = line.pop()
      for m in sorted(allmeas):
        if m in samples.keys(): line.append(samples[m])
        else:                   line.append("")
      mkreport.writerow(line)
      
      if not options.verbose: 
        i += 1
        j = len(report)
        gcmstoolbox.printProgress(i, j)
      
  print(" => Wrote " + outfile) 
  """


   ### SAVE OUTPUT JSON
   
  print("\nSaving data...")
  
  data['info']['mode'] = "components"
  data["info"]["cmds"].append(cmd)
  gcmstoolbox.saveJSON(data, options.jsonout)     # backup and safe json
  
  print(" => Wrote " + options.jsonout + "\n")
  exit()
  
    
if __name__ == "__main__":
  main()