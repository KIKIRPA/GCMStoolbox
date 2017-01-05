#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import OrderedDict


def main():
  print(  "GCMStoolbox")
  print(  "  This file contains common functions for the GCMStoolbox scripts,")
  print(  "  and cannot be used directly. \n")
  

# GCMStoolbox version
version = "1.9.1"
date    = " 5 Jan 2017"  #12 chars!


# ELinC resin names
resin = { "BLK0000": "BLA",
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

  
  

def normalise(xydata, norm = 999, verbose = False):
  # normalises the spectrum to the highest value of normval (999)
  
  maxy = max(xydata.values())
  
  if maxy != norm:
    if verbose: print("    - Max Y value: " + str(maxy) + " -> normalise...")
    for x, y in xydata.items():
      xydata[x] = int(round(y * norm / maxy))
      
  # remove all couples with y=0
  for key in list(xydata.keys()):
    if xydata[key] == 0:
      del xydata[key]




    


def sumspectrum(*spectra, name="sum"):
  xysum = {}
  rilist = []
  
  #process the individual spectra
  for sp in spectra:
    #RI
    if 'RI' in sp:
      ri = float(sp['RI'])
    else:
      ri = extractRI(sp['Name'])
    if ri != 0:
      rilist.append(ri)
    #xydata
    for x, y in sp['xydata'].items():
      if x not in xysum:
        xysum[x] = y
      else:
        xysum[x] = xysum[x] + y
  
  # TODO? normalise to 999
  
  # average RI
  if len(rilist) > 0:
    ri = sum(rilist) / float(len(rilist))
  else:
    ri = 0
    
  # delta RI
  d = max(rilist) -  min(rilist)
    
  # output a very basic spectrum: name, RI (if available), numpeaks and xydata
  sp = {}
  sp['Name'] = name
  if ri != 0:
    sp['Name'] += " RI=" + str(round(ri,2))
    sp['RI'] = str(round(ri,2))
    sp['Comments'] = "RI=" + str(round(ri,2)) + " dRI=" + str(round(d,2))
  sp['Num Peaks'] = len(xysum)
  sp['xydata'] = xysum
  
  return sp





def extractRI(name):
  if "RI=" in name:
    ri = name.split("RI=", 1)[1]
    ri = ri.split(" ", 1)[0]
    ri = float(ri.strip())
  else:
    ri = 0
  return ri


 
 

# Print iterations progress
def printProgress (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 50):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    formatStr = "{0:." + str(decimals) + "f}"
    percent = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = '█' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percent, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()



    
if __name__ == "__main__":
  main()
