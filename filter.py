#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from collections import OrderedDict
from optparse import OptionParser, OptionGroup
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Version: {} ({})                                             *".format(gcmstoolbox.version, gcmstoolbox.date))
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *")
  print(  "*   Licence: GNU GPL version 3                                                *")
  print(  "*                                                                             *")
  print(  "* FILTER                                                                      *")
  print(  "*   Reduces the groups json file based on a number of filtering options       *") 
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  ### OPTIONPARSER
  
  usage = "\n\nCommands:\n"
  usage += "  list    Overview of defined filters\n"
  usage += "           --> usage: %prog list [options]\n"
  usage += "  on      Enable filter\n"
  usage += "           --> usage: %prog on [options] FILTER_NUMBERS\n"
  usage += "  off     Disable filter\n"
  usage += "           --> usage: %prog off [options] FILTER_NUMBERS\n"
  usage += "  make    Define a new filter\n"
  usage += "           --> usage: %prog make [options]"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose",    help="Be very verbose",  action="store_true", dest="verbose", default=False)
  parser.add_option("-i", "--jsonin",  help="JSON input file name [default: gcmstoolbox.json]", action="store", dest="jsonin", type="string", default="gcmstoolbox.json")
  parser.add_option("-o", "--jsonout", help="JSON output file name [default: same as JSON input file]", action="store", dest="jsonout", type="string")
  
  group = OptionGroup(parser, "MAKE: Filter out groups based on group number")
  group.add_option("-g", "--group",       help="Group number [default: 0], multiple possible", action="append", dest="group", type="string")
  parser.add_option_group(group)
  
  group = OptionGroup(parser, "MAKE: Filter out groups on the number of spectra in a group")
  group.add_option("-c", "--count",      help="Minimal number of spectra per group", action="store", dest="count", type="int")
  group.add_option("-C",                 help="Don't count multiple spectra from the same source", action="store_true", dest="sourcecount", default=False)
  parser.add_option_group(group)
  
  group = OptionGroup(parser, "MAKE: Filter out groups based on the presence of a chosen m/z")
  group.add_option("-m", "--mass",       help="m/z value, multiple possible", action="append", dest="mass", type="int")
  group.add_option("-M", "--percent",    help="Minimal relative intensity of a m/z value [default: 90]", action="store", dest="percent", type="int", default=90)
  group.add_option("-s", "--sum",        help="Calculate sumspectra with the N spectra with highest signal, 0 for all [default: 0]", action="store",  dest="n", type="int", default=0)
  parser.add_option_group(group)
  
  (options, args) = parser.parse_args()
  
  
  ### ARGUMENTS AND OPTIONS
  
  cmd = " ".join(sys.argv)

  if options.verbose: print("Processing arguments...")
  
  # check and read JSON input file
  data = gcmstoolbox.openJSON(options.jsonin)
  if data['info']['mode'] == 'spectra':
    print("\n!! Cannot filter on ungrouped spectra.")
    exit()
  
  # json output 
  if options.jsonout == None: 
    options.jsonout = options.jsonin

  if options.verbose:
    print(" => JSON input file:  " + options.jsonin)
    print(" => JSON output file: " + options.jsonout + "\n")
    
  # command and arguments
  if len(args) == 0:
    print(" !! No command given\n")
    exit()
  elif args[0].lower().startswith("l"):
    if len(args) > 1:
      print(" !! The list command does not support arguments\n")
      exit()
    else: #LIST
      for id, it in data['filters'].items():
        print(id + ": filters out " + str(len(it['out'])) + " groups [" + ("Enabled" if it['active'] else "Disabled") + "]")
        if 'crit1' in it: print("  - remove groups: " + it['crit1'])
        if 'crit2' in it: print("  - remove on spectrum count: " + it['crit2'])
        if 'crit3' in it: print("  - remove on m/z values: " + it['crit3'])
        print('')
      exit()
  elif (args[0].lower() == 'on') or (args[0].lower() == 'off'):
    flist = [x.upper() for x in args]
    act = True if (flist.pop(0) == 'ON') else False
    safe = False
    for f in flist:
      if not f.startswith("F"): f = "F" + f
      if f in data['filters']:
        data['filters'][f]['active'] = act
        print(('Enabled ' if act else 'Disabled ') + f)
        safe = True
    if safe:
      data["info"]["cmds"].append(cmd)
      gcmstoolbox.saveJSON(data, options.jsonout)     # backup and safe json
      print(" => Updated " + options.jsonout + "\n")
    else:
      print(" !! Invalid filter names\n")
    exit()
  elif args[0].lower().startswith("m"):
    if len(args) > 1:
      print(" !! The list command does not support arguments\n")
      exit()
    # else: proceed
  else:
    print(" !! Invalid command given\n")
    exit()
    
  #criterium flags
  c1 = False if options.group is None else True  #CRITERIUM1: group numbers to be removed
  c2 = False if options.count is None else True  #CRITERIUM2: minimal spectrum count per group 
  c3 = False if options.mass  is None else True  #CRITERIUM3: minimal intensity of choses m/z values

  if not (c1 or c2 or c3):
    print("\n!! No criteria selected. Nothing to do.")
    exit()

    
  ### INITIALISE

  candidates = set(data["groups"].keys())
  # candidates for removal; each criterium will remove those groups that should be kept
  # since we iterate through a set that will be smaller after each criterium, we'll do the
  # most time-consuming criteria last
  
  
  ### CRITERIUM 1: GROUP NUMBER
  if c1:
    removegroups = []
    for g in options.group:
      g = str(g).upper()
      if not g.startswith('G'): g = "G" + g
      removegroups.append(g)
    
    print("\nCRITERIUM 1: remove groups by group numbers: " + ", ".join(removegroups))
    if not options.verbose: 
      i = 0
      j = len(candidates)
      gcmstoolbox.printProgress(i, j)
      
    for c in list(candidates):   # iterate over a copy of the set, so we can remove things from the original while iterating
      if c not in removegroups:
        candidates.discard(c)
        
      # progress bar
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
  
    if options.verbose: 
      print("candidates for removal:")
      if len(candidates) == 0:
        print("  none")
      else:
        print(tabulate(candidates))

  
  ### CRITERIUM 2: SPECTRUM COUNT
  if c2:
    print("\nCRITERIUM 2: remove groups with less than " + str(options.count) + " spectra...")
    if not options.verbose: 
      i = 0
      j = len(candidates)
      gcmstoolbox.printProgress(i, j)
      
    for c in list(candidates):   # iterate over a copy of the set, so we can remove things from the original while iterating
      if not options.sourcecount:
        # count number of spectra
        if data["groups"][c]["count"] >= options.count:  #remove from candidates = keep group
          candidates.discard(c)
      else:
        # count number of sources
        spset = set()
        nosource = 0   # also count spectra without source
        for s in data["groups"][c]["spectra"]:
          if "Source" in data["spectra"][s]:
            spset.add(data["spectra"][s]["Source"])
          else:
            nosource += 1
        if (len(spset) + nosource) >= options.count:  #remove from candidates = keep group
          candidates.discard(c)
        
      # progress bar
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
  
    if options.verbose: 
      print("candidates for removal:")
      if len(candidates) == 0:
        print("  none")
      else:
        print(tabulate(candidates))


  ### CRITERIUM 3: RUBBISH PEAK SEARCH
  if c3:
    print("\nCRITERIUM 3: remove groups with m/z value " + ", ".join(str(m) for m in options.mass))
    if not options.verbose: 
      i = 0
      j = len(candidates)
      gcmstoolbox.printProgress(i, j)
      
    for c in list(candidates):
      # read the spectra in this group
      splist = []
      for s in data['groups'][c]['spectra']: 
        splist.append(data['spectra'][s])
      
      # if more than one spectrum, make sumspectrum
      if len(splist) > 1:
        sumsp = gcmstoolbox.sumspectrum(*splist, highest = options.n)
      else:
        sumsp = splist[0]
        
      # check masses
      remove = False     
      maxval = max(sumsp['xydata'].values())
      for m in options.mass:
        if str(m) in sumsp['xydata']:
          if int(sumsp['xydata'][str(m)]) > (maxval * 0.01 * options.percent):     #remove group
            if options.verbose:
              print(" --> G" + c + " m/z=" + str(m) + " y-value=" + str(sumsp['xydata'][str(m)]) + " threshold=" + str(maxval * 0.01 * options.percent))
            remove = True

      # final decission
      #if a group is tagged for removal, we need to keep it in the candidates set! if it is not tagged for removal, we eliminate it as a candidate
      if not remove:  
        candidates.discard(c)
        
      # progress bar
      if not options.verbose: 
        i += 1
        gcmstoolbox.printProgress(i, j)
      
    if options.verbose: 
      print("candidates for removal:")
      if len(candidates) == 0:
        print("  none")
      else:
        print(tabulate(candidates))
    
        
  ### UPDATE GROUPS AND WRITE IT AS JSON
  
  if 'filters' not in data:
    data['filters'] = OrderedDict()
    f = "F1"
  else:
    f = "F" + str(len(data['filters']) + 1)
    
  data['filters'][f] = OrderedDict()
  if c1: data['filters'][f]['crit1'] = ", ".join(removegroups)
  if c2: data['filters'][f]['crit2'] = str(options.count)
  if c3: data['filters'][f]['crit3'] = "m/z " + ", ".join(str(m) for m in options.mass) + "; " + str(options.percent) + "%; " + str(options.n)
  data['filters'][f]['active'] = True
  data['filters'][f]['out'] = sorted(candidates)

  print("\nFilter " + f)
  print("  - initial number of groups:  " + str( len(data['groups']) ))
  print("  - number of removed groups:  " + str( len(candidates) ))
  print("  - number of retained groups: " + str( len(data['groups']) - len(candidates) ))

  af = []
  ac = set()
  for f, filter in data['filters'].items():
    if filter['active']:
      af.append(f)
      ac.update(filter['out'])
  
  print("\nAll active filters (" + ", ".join(af) + ")")
  print("  - initial number of groups:  " + str( len(data['groups']) ))
  print("  - number of removed groups:  " + str( len(ac) ))
  print("  - number of retained groups: " + str( len(data['groups']) - len(ac) ))

  data['info']['mode'] = "filter"
  data["info"]["cmds"].append(cmd)
  gcmstoolbox.saveJSON(data, options.jsonout)     # backup and safe json
  
  print(" => Finalised. Wrote " + options.jsonout + "\n")
  exit()

  
    
    
def tabulate(words, termwidth=79, pad=3):
  words = sorted(int(x) for x in words)
  words = list(str(x) for x in words)
  width = len(max(words, key=len)) + pad
  ncols = max(1, termwidth // width)
  nrows = (len(words) - 1) // ncols + 1
  table = []
  
  for i in range(nrows):
    row = words[i::nrows]
    format_str = ('%%-%ds' % width) * len(row)
    table.append(format_str % tuple(row))
  return '\n'.join(table)



    
if __name__ == "__main__":
  main()
