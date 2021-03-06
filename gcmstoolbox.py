#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pprint
import json
import time
from collections import OrderedDict


def main():
  print(  "GCMStoolbox")
  print(  "  This file contains common functions for the GCMStoolbox scripts,")
  print(  "  and cannot be used directly. \n")
  

# GCMStoolbox version
version = "4.2   "       #6 chars!
date    = "11 Jul 2020"  #11 chars!


# ELinC resin names
resin = { "BLANCO":  "B",
          "BLK0001": "TR",
          "BLK0002": "LA",
          "BLK0004": "MNC",
          "BLK0005": "PC",
          "BLK0007": "S",
          "BLK0008": "C",
          "BLK0009": "AB",
          "BLK0012": "MAS",
          "BLK0013": "G",
          "BLK0014": "E",
          "BLK0017": "KC",
          "BLK0026": "COP",
          "BLK0028": "SB",
          "BLK0029": "SSE",
          "BLK0031": "SST",
          "BLK0032": "BE1",
          "BLK0040": "TN",
          "BLK0041": "LI",
          "BLK0044": "STR",
          "BLK0045": "EAC",
          "BLK0048": "SA2",
          "BLK0065": "HN",
          "BLK0066": "HF",
          "BLK0067": "CC",
          "BLK0070": "MDC",
          "BLK0079": "DA",
          "BLK0080": "DR",
          "REF0023": "AM",
          "REF0072": "TP",
          "REF0091": "ZC",
          "REF0092": "ZC",
          "REF0130": "BE2",
          "REF0145": "DR",
          "REF0146": "AM",
          "REF0148": "BE2",
          "REF0149": "DR",
          "REF0150": "SP",
          "REF0152": "STR",
          "REF0160": "SA1",
          "REF0161": "PT",
          "REF0163": "SA1",
          "REF0175": "AM",
          "REF0185": "SA1",
          "REF0190": "PT",
          "REF0202": "ZC",
          "REF0203": "ZC",
          "REF0208": "BE2",
          "REF0209": "BE2",
          "REF0215": "TP",
          "REF0218": "DR",
          "REF0224": "AM",
          "REF0233": "SA1"          
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





def sumspectrum(*spectra, signal="IS", highest=False):
 
  ### calculate signals
  
  signals = []
  spectra2 = {}   #combine signals and spectra 
  
  for sp in spectra:
    if signal in sp: signals.append(float(sp[signal]))
    else           : signals.append(0)
  
  maxsignal = max(signals)
  minsignal = maxsignal
  for s in signals:
    if (s < minsignal) and (s != 0): minsignal = s

  # give the spectra without a signal, a value that is 0.1 times that of the lowest
  if maxsignal != 0:
    signals = [((minsignal*0.1) if s==0 else s) for s in signals]
  else:
    signals = [1 for s in signals] #if however all signals are 0 (no IS set), all 1
  
  #combine signals and spectra
  for i in range(len(signals)):
    spectra2[signals[i]] = spectra[i]
  
  ### reduce spectra2 to the highest signals
  
  spectra3 = {}
  if highest:
    signals = sorted(signals, reverse=True)
    limit = signals[((highest-1) if len(signal) >= highest else (len(signal) - 1))]
    for si, sp in spectra2.items():
      if si >= limit:
        spectra3[si] = sp
  else:
    spectra3 = spectra2
    
  ### make sumspectrum      
  
  xysum = {}
  rilist = []
  
  #process the individual spectra
  for si, sp in spectra3.items():
    #RI
    if 'RI' in sp: rilist.append(float(sp['RI']))
    
    #xydata
    for x, y in sp['xydata'].items():
      if x not in xysum:
        xysum[x] =si * y
      else:
        xysum[x] = xysum[x] + si * y
  
  # normalise to 999
  normalise(xysum)
  
  # average RI
  if len(rilist) > 0:
    ri = sum(rilist) / float(len(rilist))
  else:
    ri = 0
    
  # delta RI
  d = max(rilist) -  min(rilist)
    
  # output a very basic spectrum: RI (if available), numpeaks and xydata
  sp = OrderedDict()
  if ri != 0:
    sp['RI'] = str(round(ri,1))
    sp['dRI'] = str(round(d,1))
  sp['Num Peaks'] = len(xysum)
  sp['xydata'] = xysum
  
  return sp



 
 

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


def openJSON(jsonin):
  if not os.path.isfile(jsonin):
    print("  !! " + jsonin + " was not found.\n")
    exit()
  with open(jsonin,'r') as fh:
    data = json.load(fh, object_pairs_hook=OrderedDict)
  return data
    

    
def saveJSON(data, jsonout):
  #backup
  if os.path.isfile(jsonout):
    os.rename(jsonout, jsonout + time.strftime("%Y%m%d%H%M%S"))
  #safe new JSON file
  with open(jsonout,'w') as fh:
    fh.write(json.dumps(data, indent=2))

    
if __name__ == "__main__":
  main()
