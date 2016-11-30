#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from glob import glob
from optparse import OptionParser, OptionGroup


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (30 Nov 2016) *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* CONVERT:                                                                    *")
  print(  "*   convert AMDIS files (.msl, .csl, .isl) to a NIST MS SEARCH file (.msp)    *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")

  shortdescr = ("Converts INFILES MSP file format. Multiple INFILES can be supplied by using\n"
                "wildcards (?,*) and will be converted into one single MSP file. If no OUTFILE is\n"
                "given, either the filename of the single input file will be used, or joined.msp\n"
                "will be used in case of multiple input files.")

  ### OPTIONPARSER
  
  usage = "usage: %prog [options] INFILES"
  parser = OptionParser(usage, version="%prog 0.4")
  parser.add_option("-v", "--verbose", help="Be very verbose", action="store_true", dest="verbose", default=False)
  parser.add_option("-o", "--outfile", help="output file name", action="store", dest="outfile", type="string")
  parser.add_option("-a", "--append", help="append to output file", action="store_true", dest="append",  default=False)
  parser.add_option("-e", "--elinc", help="Special formatting for ELinC data. Extra parameters are retrieved from the structured file names and are used to set custom MSP fields, adapted spectrum names and sources", action="store_true", dest="elinc", default=False)
  (options, args) = parser.parse_args()

  ### ARGUMENTS

  if options.verbose: print("Processing INFILES and options")

  if len(args) == 0:
    exit()

  # make a list of input files
  inFiles = []
  for arg in args:
    inFiles.extend(glob(arg))
  inFiles = list(set(inFiles)) #remove duplicates
  for inFile in inFiles:
    if os.path.isdir(inFile):
      inFiles.remove(inFile)   #remove directories
    else:
      if options.verbose: print(" - input file: " + inFile)

  # number of inFiles; must not be 0
  numInFiles = len(inFiles)
  if numInFiles == 0:
    parser.error("No input files?")
    exit()
  else:
    if options.verbose: print(" => " + str(numInFiles) + " input files")
    
  if options.outfile != None:
    outFile = options.outfile
  elif numInFiles == 1:
    outFile = os.path.splitext(os.path.basename(inFiles[0]))[0] + ".msp"
  else:
    outFile = "joined.msp"

  if options.verbose: print(" => output file: " + outFile + (" [append]" if options.append else ""))

  if options.elinc and options.verbose: print(" => ELinC special formatting is set")
  
  ### OPEN OUTPUT FILE
  
  if options.append:
    fho = open(outFile, mode='a')
  else:
    fho = open(outFile, mode='w')
  
  ### ITERATE THROUGH INFILES
  
  i = 1 # spectrum number
  
  for inFile in inFiles:
    print("\nProcessing file: " + inFile)
    with open(inFile,'r') as fhi:   #file handle closes itself 
      while True:
        # read spectra
        sp = readspectrum(fhi, i, options.verbose)
        if not sp: break   # break from while loop if readspectrum returns False (<= EOF)
        
        # apply special ELinC formatting
        if options.elinc:
          sp = elincize(sp, inFile, verbose=options.verbose)
        
        # write spectrum
        if (options.append) or (i > 1):     #always start with an emtpy line, except for the first spectrum in a new file (not append)
          fho.write("\n")
        writespectrum(fho, sp, options.verbose)
        
        # increase spectrum number
        i = i + 1
        
  # close output file 
  print("\nFinalised. Wrote " + outFile + "\n")
  fho.close()
  exit


      
    

def readspectrum(fh, i, verbose = False):
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
      xSeries = []
      ySeries = []
      
      #verbose
      if verbose:
        print(" - Reading spectrum " + str(i) + ": " + spectrum.get('Name'))
      
      for nextline in fh:
        nextline = nextline.strip() #remove newline and other spaces from the end (and beginning)
        
        if nextline == "":  #neglect empty lines, even within a spectrum
          pass  
        
        elif nextline.casefold().startswith('num peaks'):  #numpeaks: switch from readmeta to readdata mode
          numpeaks = int(nextline.split(':', 1)[1].strip())
          spectrum['Num Peaks'] = numpeaks
          readmeta = False
          readdata = True
        
        elif nextline.casefold().startswith('cas#'):
          #NOTE: NIST seems to store sometimes CAS# and NIST# on the same line, CAS# first and then NIST# 
          #      separated with semicolon. I haven't seen AMDIS doing this. I hope this is the only case?
          if 'nist#' in nextline.casefold():
            parts = nextline.split(';', 1)
            spectrum["CAS#"]  = parts[0].split(':', 1)[1].strip()
            spectrum["NIST#"] = parts[1].split(':', 1)[1].strip()
          else:
            spectrum["CAS#"]  = nextline.split(':', 1)[1].strip()
      
        elif readmeta:     #all metadata
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
          nextline = nextline.replace("(", "").replace(")", ";")
          
          #prepare for splitting
          if nextline[-1:] == ";":      #remove ; from the end of the line (if present)
            nextline = nextline[:-1]
          
          #split into X-Y couples, separate values and append to x and y series
          couples = nextline.split(";")
          for couple in couples:
            x, y = couple.split(None, 1)   #None should split on multiple whitespaces
            xSeries.append(int(x.strip()))
            ySeries.append(int(y.strip()))
          
          #countdown numpeaks and prepare to end this function
          numpeaks = numpeaks - len(couples)
          if numpeaks == 0:
            #one more thing: is this ySeries normalised?
            #Amdis normalises to 1000, NIST to 999
            #if normalised to 1000, just change this value(s) to 999 (very small error)
            #if not normalised, we won't touch it
            if max(ySeries) == 1000:
              ySeries = [999 if y == 1000 else y for y in ySeries]
              if verbose: print("     ! 1000 -> 999...") 
            elif max(ySeries) == 999:
              pass
            else:
              if verbose: print("      ! Spectrum is unnormalised. Max Y: " + str(max(ySeries)) + " Did not touch...")      
            #add series to the spectrum dictionary    
            spectrum['xSeries'] = xSeries
            spectrum['ySeries'] = ySeries
            spectrum['DB#'] = str(i)
            #finished!
            return spectrum
  
  # if all lines are processed
  return False



def elincize(sp, inFile, separator = "-", verbose = False):
  # special formatting for ELinC data
  #  - retrieve SAMPLECODE, AGING, COLOR, TEMPPROG from filename
  #      e.g S-BLK0065-8-0B-HymCFresh-160531-480-di-med.msl
  #          | |       | |  |         |      |   |__|________ 7+8 [not used]     AMDIS parameter set
  #          | |       | |  |         |      |_______________ 6   PY PROG        pyrolysis temperature program
  #          | |       | |  |         |______________________ 5   [not used]     analysis date
  #          | |       | |  |________________________________ 4   SAMPLE DESCR   sample description
  #          | |       | |___________________________________ 3   AGING + COLOR  days of artificial aging and sample color
  #          | |_______|_____________________________________ 1+2 SAMPLE CODE    code of the sample glass plate
  #          |_______________________________________________ 0   [not used]         
  #  - build new NAME
  #  - build new SOURCE
  
  #verbose
  if verbose:
    print("    - ELinCize spectrum")
  
  #split filename
  base = os.path.splitext(os.path.basename(inFile))[0] #strip path and extension
  parts = base.split(separator)
  
  if len(parts) < 7:
    print("      ! ELinCize failed: not enough parts in " + base + "\n")
    exit()
  
  #rebuild existing fields
  sp['Name']     = "S" + sp['DB#'] + " RI=" + sp['RI'] + " " + parts[1] + "-" + parts[2] + "-" + parts[3] + "-" + parts[6]
  sp['Source']   = os.path.basename(inFile)
  sp['Comments'] = ('Sample="' + parts[0] + '-' + parts[1] + '-' + parts[2] + '" '
                     + 'Aging="' + parts[3][:-1] + ' days" '
                     + 'Color="' + ("black" if parts[3][-1:].upper() == "B" else "unpigmented") + '" '
                     + 'Description="' + parts[4] + '" '
                     + 'PyTemp="' + parts[6] + '" '
                    )
    
  return sp




def writespectrum(fh, sp, verbose = False):
  # write the spectrum to the file handle line by line in NIST MSP format
  # don't mind to much about the order of the lines; we start with Name, and end with NumPeaks and the spectral data
  
  #verbose
  if verbose:
    print("    - Write spectrum in output file")
  
  #start with the Name field (and remove it from the dictionary)
  fh.write('Name: '   + sp.pop('Name', 'None') + "\n")
  
  #remove the fields that will be written at the end
  numpeaks = sp.pop('Num Peaks')
  xSeries  = sp.pop('xSeries')
  ySeries  = sp.pop('ySeries')
  
  #then iterate over the remaining items
  for key, value in sp.items():
    fh.write(key + ': ' + value + "\n")
  
  # write NumPeaks
  fh.write('Num Peaks: ' + str(numpeaks) + "\n")
  
  # NIST MSP puts 5 couples on each line
  # 1. iterate over full lines
  div = numpeaks // 5          # we have %div full lines
  for i in range(div):         
    line = ""  
    for j in range(5): 
      line = line + str(xSeries.pop(0)) + " " + str(ySeries.pop(0)) + "; "
    fh.write(line.rstrip(" ") + "\n")
  # 2. iterate over full lines
  mod = numpeaks % 5           # the last line will have mod couples
  line = ""
  for i in range(mod):
    line = line + str(xSeries.pop(0)) + " " + str(ySeries.pop(0)) + "; "
  fh.write(line.rstrip(" ") + "\n")
    


  
    
if __name__ == "__main__":
  main()
