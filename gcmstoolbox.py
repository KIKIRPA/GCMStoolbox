#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

def main():
  print(  "GCMStoolbox")
  print(  "  This file contains common functions for the GCMStoolbox scripts,")
  print(  "  and cannot be used directly. \n")
  

# GCMStoolbox version
version = "1.9.0"
date    = " 4 Jan 2017"  #12 chars!



def readspectrum(fh, i = 0, match = [], norm = 999, elu = False, eluAll = False, verbose = False):
  # we expect that each spectrum starts with 'name' (case insensitive)
  # we use this as a trigger to start recording the metadata, reading the filehandle line by line
  # once we read 'num peaks' we start collecting the spectrum itself, counting the number
  # once numpeaks is reached, we return the data as a dictonary
  
  for line in fh: 
    if line.casefold().startswith('name'):
      #initialize some data
      spectrum = {'Name': line.split(':', 1)[1].strip()}  #define a dictionary
      readmeta = True
      readdata = False
      xy = {}       
      
      #match: list of spectrum names: only return spectrum for those, "no match" for others
      if (len(match) > 0) and (spectrum["Name"] not in match):
        return "no match"
      
      if elu:
        # example "|SC15|CN2|MP1-MODN:81(%84.3)|AM25664|PC32|SN27|WD5.4|TA4.5|TR14.0|FR12-20|RT2.1366|MN2.7|RA0.00403|IS394917|XN425813|RI740.7|MO4: 81 79 77 96|EW1-0|FG0.843|TN3.585|OR1|NT1"
        eluNameParts = spectrum['Name'].split('|')
        for p in eluNameParts:
          if p.startswith('RI'): spectrum['RI'] = p[2:]  # retention index
          if p.startswith('RT'): spectrum['RT'] = p[2:]  # retention time
          if p.startswith('IS'): spectrum['IS'] = p[2:]  # integrated signal (deconvoluted peakarea)
          if p.startswith('RA'): spectrum['RA'] = p[2:]  # relative amount to TIC
          if p.startswith('OR'): spectrum['OR'] = p[2:]  # order number of Amdis models (starts with 1)
        # don't proceed if this is not the first order model (and if eluAll is False)
        if (not eluAll) and (spectrum['OR'] != "1"):
          return "no match"   
        spectrum["Comments"] = "RI=" + spectrum['RI'] + " RT=" + spectrum['RT'] + " IS=" + spectrum['IS'] + " RA=" + spectrum['RA'] + " OR=" + spectrum['OR']
      
      #verbose
      if verbose:
        if i != 0: print(" - Reading spectrum " + str(i) + ": " + spectrum.get('Name'))
        else:      print(" - Reading spectrum: " + spectrum.get('Name'))
      
      for nextline in fh:
        nextline = nextline.strip() #remove newline and other spaces from the end (and beginning)
        
        if nextline == "":  #neglect empty lines, even within a spectrum
          pass  
        
        elif nextline.casefold().startswith('num peaks'):  #numpeaks: switch from readmeta to readdata mode
          numpeaks = int(nextline.split(':', 1)[1].strip())
          spectrum['Num Peaks'] = numpeaks
          readmeta = False
          readdata = True
          
        elif readmeta and not elu: #all metadata in ELU files is contained within the name string! if elu -> skip these lines until the NumPeaks line
          if nextline.casefold().startswith('cas#'):
            #NOTE: NIST seems to store sometimes CAS# and NIST# on the same line, CAS# first and then NIST# 
            #      separated with semicolon. I haven't seen AMDIS doing this. I hope this is the only case?
            if 'nist#' in nextline.casefold():
              parts = nextline.split(';', 1)
              spectrum["CAS#"]  = parts[0].split(':', 1)[1].strip()
              spectrum["NIST#"] = parts[1].split(':', 1)[1].strip()
            else:
              spectrum["CAS#"]  = nextline.split(':', 1)[1].strip()
          
          else:     #all other metadata
            #NOTE: I assume that each metadata field is restrained to a single line; I haven't seen any
            #      multiline field so far. This code only supports single lines!
            #NOTE: We don't support multiple "Synon" tags as in the NIST MSP files
            #      (if we would implement it, we need to put those in a list/array)
            parts = nextline.split(':', 1)
            parts[0] = parts[0].strip().title()       # field name: each first letter is capilalised in NIST
            if parts[0] == "Casno": parts[0] = "CAS#" # exception: CASNO in Amdis translates into CAS# in NIST
            if parts[0] == "Nist#": parts[0] = "NIST#"
            if parts[0] == "Db#":   parts[0] = "DB#"
            if parts[0] == "Ri":    parts[0] = "RI"
            if parts[0] == "Rt":    parts[0] = "RT"
            if parts[0] == "Mw":    parts[0] = "MW"
            if parts[0] == "Exactmass": parts[0] = "ExactMass"
            spectrum[parts[0]] = parts[1].strip()
        
        elif readdata:    # read spectral data
          #rough conversion from Amdis bracket-style to NIST semicolon style
          nextline = nextline.replace("(", "").replace(")", ";").replace(",", " ")
          
          #prepare for splitting
          if nextline[-1:] == ";":      #remove ; from the end of the line (if present)
            nextline = nextline[:-1]
          
          #split into X-Y couples, separate values and append to x and y series
          #ELU files might have something extra, which we will discard
          couples = nextline.split(";")
          for couple in couples:
            couple = couple.split(None)   #None should split on multiple whitespaces
            xy[int(couple[0].strip())] = int(couple[1].strip())
          
          #countdown numpeaks and prepare to end this function
          numpeaks = numpeaks - len(couples)
          if numpeaks == 0:            
            #normalisation
            if norm > 0: 
              normalise(xy, norm, verbose)
            elseif (max(xy.values()) != 999) and verbose:
              print("      ! Spectrum is unnormalised. Max Y: " + str(max(xy.values())) + " Did not touch...")
      
            #add series to the spectrum dictionary    
            spectrum['xydata'] = xy
            if i != 0: spectrum['DB#'] = str(i)
            
            #finished!
            return spectrum
  
  # if all lines are processed
  return "eof"
  
  

def normalise(xydata, norm = 999, verbose = False):
  # normalises the spectrum to the highest value of normval (999)
  
  maxy = max(xydata.values())
  
  if maxy != norm:
    if verbose: print("      - Max Y value: " + str(maxy) + " -> normalise...")
    for x, y in xydata.items():
      xydata[x] = int(y * norm / maxy)
      
  #return xydata  # this dict is called by reference? no need to return it?
  



def writespectrum(fh, sp, verbose = False):
  # write the spectrum to the file handle line by line in NIST MSP format
  # don't mind to much about the order of the lines; we start with Name, and end with NumPeaks and the spectral data

  #remove the fields that will be written at the end
  name     = sp.pop('Name', 'None')
  numpeaks = sp.pop('Num Peaks')
  xydata   = sp.pop('xydata')
  
  #verbose
  if verbose:
    print("    - Write", name, "in output file")
  
  
  #start with the Name field (and remove it from the dictionary)
  fh.write('Name: '   + name + "\n")
  
  #then iterate over the remaining items
  for key, value in sp.items():
    fh.write(key + ': ' + value + "\n")
  
  # write NumPeaks
  fh.write('Num Peaks: ' + str(numpeaks) + "\n")
  
  # NIST MSP puts 5 couples on each line
  # 1. iterate over full lines
  div = numpeaks // 5          # we have %div full lines
  xvalues = sorted(xydata.keys())
  for i in range(div):         
    line = ""  
    for j in range(5): 
      x = xvalues.pop(0)
      y = xydata[x]
      line = line + str(x) + " " + str(y) + "; "
    fh.write(line.rstrip(" ") + "\n")
  # 2. iterate over the last incomplete line
  mod = numpeaks % 5           # the last line will have mod couples
  if mod > 0:
    line = ""
    for i in range(mod):
      x = xvalues.pop(0)
      y = xydata[x]
      line = line + str(x) + " " + str(y) + "; "
    fh.write(line.rstrip(" ") + "\n")
  fh.write("\n")
    


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
