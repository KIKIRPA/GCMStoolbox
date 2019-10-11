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

