#! /usr/bin/env python
# -*- coding: utf-8 -*-

#import sys
#import os
#import csv
import re
#from glob import glob
from optparse import OptionParser, OptionGroup
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Version: {} ({})                                             *".format(gcmstoolbox.version, gcmstoolbox.date))
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage               *")
  print(  "*   Licence: GNU GPL version 3                                                *")
  print(  "*                                                                             *")
  print(  "* NIST2TXT  :                                                                 *")
  print(  "*   converts one or more spectra in .MSP and .MSL files to text format        *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")


  ### OPTIONPARSER
  
  usage = "usage: %prog [options] NISTFILE"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose", help="Be very verbose [not default]", action="store_true", dest="verbose", default=False)
  parser.add_option("-n", "--name",    help="Search spectra on name", action="store", dest="search_name", type="string")
  parser.add_option("-r", "--ri",      help="Search on retention index", action="store", dest="search_ri", type="string")
  parser.add_option("-c", "--cas",     help="Search on CAS number", action="store", dest="search_cas", type="string")
  
  (options, args) = parser.parse_args()


  ### ARGUMENTS AND OPTIONS

  # make a list of input files
  if len(args) == 0:
    print(" !! No NIST file?\n")
    exit()
  elif len(args) > 1:
    print(" !! Too many NIST files!\n")
    exit()
  else:
    inFile = args[0]
  

  ### READ FILE
  if options.verbose: print("\nProcessing file: " + inFile)
  
  with open(inFile,'r') as fh:   #file handle closes itself
    for line in fh: 
    
      # FIRST LINE
      if line.casefold().startswith('name'):
        name = line.split(':', 1)[1].strip()
        ri = ""
        cas = ""
        count = 0
        values = []

        # OTHER METADATA
        for nextline in fh:
          if nextline.casefold().startswith('cas#'):
              #NOTE: NIST seems to store sometimes CAS# and NIST# on the same line, CAS# first and then NIST# 
              #      separated with semicolon. I haven't seen AMDIS doing this. I hope this is the only case?
              if 'nist#' in nextline.casefold():
                parts = nextline.split(';', 1)
                cas = parts[0].split(':', 1)[1].strip()
              else:
                cas = nextline.split(':', 1)[1].strip()
          elif nextline.casefold().startswith('ri'):
            ri = nextline.split(':', 1)[1].strip()
          elif nextline.casefold().startswith('num peaks'):
            count = int(nextline.split(':', 1)[1].strip())
            break
        
        # EVALUATE QUERY CONDITION
        # todo

        # READ SPECTRUM
        for nextline in fh:
          #values.extend(re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", nextline))

          if len(values) * 2 == count:
            break

        # WRITE TEXT FILE
        keepcharacters = (' ','.','_')
        outfn = "".join(c for c in name if c.isalnum() or c in keepcharacters).rstrip()
        with open(outfn, "w") as outfh:
          for x in range(count):
            outfh.write(value[x*2] + ";" + value[(x*2)+1] + "\n")


if __name__ == "__main__":
  main()
