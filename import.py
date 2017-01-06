#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import ntpath
from collections import OrderedDict
from glob import glob
from optparse import OptionParser, OptionGroup
import gcmstoolbox


def main():
  print("\n*******************************************************************************")
  print(  "* GCMStoolbox - a set of tools for GC-MS data analysis                        *")
  print(  "*   Author:  Wim Fremout, Royal Institute for Cultural Heritage (" + gcmstoolbox.date + ") *")
  print(  "*   Licence: GNU GPL version 3.0                                              *")
  print(  "*                                                                             *")
  print(  "* IMPORT:                                                                     *")
  print(  "*   import one or more AMDIS (.elu, .msl, .csl, .isl) and NIST MS SEARCH      *")
  print(  "*   (.msp) files and store the mass spectra in GCMStoolbox JSON format        *")
  print(  "*                                                                             *")
  print(  "*******************************************************************************\n")


  ### OPTIONPARSER
  
  usage = "usage: %prog [options] IMPORTFILE1 [IMPORTFILE2 [...]]"
  
  parser = OptionParser(usage, version="GCMStoolbox version " + gcmstoolbox.version + " (" + gcmstoolbox.date + ")\n")
  parser.add_option("-v", "--verbose", help="Be very verbose [not default]", action="store_true", dest="verbose", default=False)
  parser.add_option("-o", "--jsonout", help="JSON output file name [default: gcmstoolbox.json]", action="store", dest="jsonout", type="string", default="gcmstoolbox.json")
  parser.add_option("-a", "--append",  help="Append to existing json file [not default]", action="store_true", dest="append",  default=False)
  
  group = OptionGroup(parser, "IMPORT OPTIONS", "Special formatting options for the ELinC project")
  group.add_option("-s", "--specno",  help="Override spectrum numbering, start with I [default: 1]; the append option may override this", action="store", dest="i", default=1, type="int")
  group.add_option("-n", "--norm",    help="Normalise to a given maximum, 0 to skip normalisation [default=999])", action="store", dest="n", default=999, type="int")
  group.add_option("--allmodels",     help="For AMDIS .ELU files: import all models [not default]", action="store_true", dest="allmodels", default=False)
  parser.add_option_group(group)
  
  group = OptionGroup(parser, "ELinC", "Special formatting options for the ELinC project")
  group.add_option("-e", "--elinc",   help="Retrieve parameters from the structured file names [not default]", action="store_true", dest="elinc", default=False)
  parser.add_option_group(group)
  
  (options, args) = parser.parse_args()

  ### ARGUMENTS AND OPTIONS
  
  cmd = " ".join(sys.argv)
  
  if options.verbose: print("Processing import files and options")

  # make a list of input files
  inFiles = []
  if len(args) == 0:
    print(" !! No import files?\n")
    exit()
  else:
    for arg in args:
      inFiles.extend(glob(arg))
  inFiles = list(set(inFiles)) #remove duplicates
  for inFile in inFiles:
    if os.path.isdir(inFile):
      inFiles.remove(inFile)   #remove directories
    else:
      if options.verbose: print(" - import file: " + inFile)

  # number of inFiles; must not be 0
  numInFiles = len(inFiles)
  if numInFiles == 0:
    print(" !! No import files?\n")
    exit()
  else:
    if options.verbose: print(" => " + str(numInFiles) + " import files")

  if options.verbose: print(" => JSON output file: " + options.jsonout + (" [append]" if options.append else ""))
 
  if options.append:
    data = gcmstoolbox.openJSON(options.jsonout)

    # check if it is a spectra file (cannot append to groups file)
    if data['info']['mode'] != "spectra": 
      print(" !! Cannot append to a '" + data['info']['mode'] + "' mode data file.\n")
      exit()
    
    # add administration to specta[0] (info)
    data['info']['cmds'].append(" ".join(sys.argv))
    data['info']['sources'].extend(inFiles)
    
    # spectrum number counter  (remark: len(spectra) is always one count higher than the number of spectra; spectra[0] is info!)
    if len(data['spectra']) < options.i:
      i = options.i
    else:
      i = len(data['spectra']) + 1
  else:
    cmds = [cmd]
    data = OrderedDict()
    data['info'] = OrderedDict([('mode', 'spectra'), ('cmds', cmds)])
    data['spectra'] = OrderedDict()
    i = options.i # spectrum number
    
  if options.elinc and options.verbose: print(" => ELinC special formatting is set")
 
  
  ### ITERATE THROUGH INFILES
  
  # init progress bar
  if not options.verbose: 
    print("\nProcessing files")
    j = 0
    k = len(inFiles)
    gcmstoolbox.printProgress(j, k)
  
  for inFile in inFiles:
    if options.verbose: print("\nProcessing file: " + inFile)

    with open(inFile,'r') as fh:   #file handle closes itself 
      while True:
        # read spectra
        inFile = os.path.basename(inFile)
        spectrum = readspectrum(fh, inFile, i, norm=options.n, allModels=options.allmodels, elinc=options.elinc, verbose=options.verbose)
        
        if spectrum == "eof": 
          break   # break from while loop if readspectrum returns False (<= EOF)
        elif spectrum != "skip":          
          # apply special ELinC formatting
          if options.elinc:
            elincize(spectrum, inFile, verbose=options.verbose)
          
          # write spectrum
          key = spectrum.pop('Name')
          data['spectra'][key] = spectrum
          
          # increase spectrum number
          i = i + 1
          
    # adjust progress bar
    if not options.verbose: 
      j += 1
      gcmstoolbox.printProgress(j, k)      
        
        
  ### WRITE SPECTRA JSON 
  
  print("\nWriting data file")
  saveJSON(data, options.jsonout)
  
  print(" => Finalised. Wrote " + options.jsonout + "\n")
  exit()



def readspectrum(fh, inFile, i = 0, norm = 999, elu = False, allModels = False, elinc=False, verbose = False):
  # we expect that each spectrum starts with 'name' (case insensitive)
  # we use this as a trigger to start recording the metadata, reading the filehandle line by line
  # once we read 'num peaks' we start collecting the spectrum itself, counting the number
  # once numpeaks is reached, we return the data as a dictonary
  
  elu = (os.path.splitext(inFile)[1][1:].strip().upper() == 'ELU')  # elu is True for .ELU files, False for others
    
  for line in fh: 
    
    # FIRST LINE
    
    if line.casefold().startswith('name'):
      
      #initialize some data
      spectrum = OrderedDict()
      spectrum['Name'] = line.split(':', 1)[1].strip()
      if i != 0: spectrum['DB#'] = str(i)
      
      readmeta = True
      readdata = False
      xy = {}
      
      #verbose
      if verbose:
        if i != 0: print(" - Reading spectrum " + str(i) + ": " + spectrum.get('Name'))
        else:      print(" - Reading spectrum: " + spectrum.get('Name'))
      
      #elu file: don't read secondary order models if not required
      if elu and not allModels:
        if "|OR1" not in spectrum['Name']: return "skip"
      
      ### NEXT LINES
      
      for nextline in fh:
        nextline = nextline.strip() #remove newline and other spaces from the end (and beginning)
        
        ### -> METADATA
        
        if readmeta:
          
          if nextline == "":  #neglect empty lines, even within a spectrum
            pass
          
          elif nextline.casefold().startswith('num peaks'):  #numpeaks: switch from readmeta to readdata mode
            # time to extract extra information for elu and elinc files 
            if elu:   eluFile(spectrum, inFile, allModels)
            if elinc: elincize(spectrum, inFile, verbose = False)
 
            # final piece of metadata; we'll add this to spectrum after normalisation and recalculation!!
            numpeaks = int(nextline.split(':', 1)[1].strip())
            #spectrum['Num Peaks'] = numpeaks
            
            # switch to readdata mode
            readmeta = False
            readdata = True
            
          elif not elu: # if elu -> skip these lines until the NumPeaks line
            if nextline.casefold().startswith('cas#'):
              #NOTE: NIST seems to store sometimes CAS# and NIST# on the same line, CAS# first and then NIST# 
              #      separated with semicolon. I haven't seen AMDIS doing this. I hope this is the only case?
              if 'nist#' in nextline.casefold():
                parts = nextline.split(';', 1)
                spectrum["CAS#"]  = parts[0].split(':', 1)[1].strip()
                spectrum["NIST#"] = parts[1].split(':', 1)[1].strip()
              else:
                spectrum["CAS#"]  = nextline.split(':', 1)[1].strip()
                      
            elif nextline.casefold().startswith('comments'):   #comments will be built by our export.py, now it would only contain duplicate info
              pass
            
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
            
        ### -> MASS SPECTRAL DATA
        
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
              gcmstoolbox.normalise(xy, norm, verbose)
            elif (max(xy.values()) != 999) and verbose:
              print("    - Spectrum is unnormalised. Max Y: " + str(max(xy.values())) + " Did not touch...")
      
            # sort in sorteddict
            xySorted = OrderedDict()
            for k in sorted(xy.keys()):
              xySorted[k] = xy[k]
            
            #add series to the spectrum dictionary    
            spectrum['Num Peaks'] = len(xySorted)
            spectrum['xydata'] = xySorted
            
            #finished!
            return spectrum
  
  # if all lines are processed
  return "eof"



def eluFile(spectrum, inFile, allModels = False):
  # example "|SC15|CN2|MP1-MODN:81(%84.3)|AM25664|PC32|SN27|WD5.4|TA4.5|TR14.0|FR12-20|RT2.1366|MN2.7|RA0.00403|IS394917|XN425813|RI740.7|MO4: 81 79 77 96|EW1-0|FG0.843|TN3.585|OR1|NT1"
  
  eluNameParts = spectrum['Name'].split('|')
  for p in eluNameParts:
    if   p.startswith('RI'): spectrum['RI'] = p[2:]  # retention index
    elif p.startswith('RT'): spectrum['RT'] = p[2:]  # retention time
    elif p.startswith('IS'): spectrum['IS'] = p[2:]  # integrated signal (deconvoluted peakarea)
    elif p.startswith('RA'): spectrum['RA'] = p[2:]  # relative amount to TIC
    elif p.startswith('SN'): spectrum['SN'] = p[2:]  # signal to noise ratio
    elif p.startswith('OR') and allModels:
                             spectrum['OR'] = p[2:]  # order number of Amdis models (starts with 1)
  
  spectrum['Source'] = inFile
  
  spectrum['Name'] = ( "S" + spectrum['DB#'] 
                       + ((" RI=" + spectrum['RI']) if 'RI' in spectrum else "")
                       + ((" IS=" + spectrum['IS']) if 'IS' in spectrum else "")
                       + ((" SN=" + spectrum['SN']) if 'SN' in spectrum else "")
                       + " " + os.path.splitext(spectrum['Source'])[0]
                     )



def elincize(spectrum, inFile, verbose = False):
  # special formatting for ELinC data
  # retrieve SAMPLECODE, AGING, COLOR, TEMPPROG from filename
  # e.g S-BLK0065-8-0B-HymCFresh-160531-480-di-med.msl
  #     | |       | |  |         |      |   |__|________ 7+8 [not used]     AMDIS parameter set
  #     | |       | |  |         |      |_______________ 6   PY PROG        pyrolysis temperature program
  #     | |       | |  |         |______________________ 5   [not used]     analysis date
  #     | |       | |  |________________________________ 4   SAMPLE DESCR   sample description
  #     | |       | |___________________________________ 3   AGING + COLOR  days of artificial aging and sample color
  #     | |_______|_____________________________________ 1+2 SAMPLE CODE    code of the sample glass plate
  #     |_______________________________________________ 0   [not used]         
  
  #verbose
  if verbose:
    print("    - ELinCize spectrum")
  
  #split filename
  base = os.path.splitext(os.path.basename(inFile))[0]   #strip path and extension
  base = base.replace("_", "-").replace(" ", "").upper() #often encountered errors in the file name
  parts = base.split("-")
  
  if len(parts) < 7:
    print("      ! ELinCize failed: not enough parts in " + base + "\n")
    exit()
  
  #(re)build fields
  spectrum['Sample'] = parts[1] + "-" + parts[2] + "-" + parts[3] + "-" + parts[6]
  spectrum['Resin']  = gcmstoolbox.resin[parts[1]]
  spectrum['AAdays'] = parts[3][:-1]
  spectrum['Color']  = parts[3][-1:]
  spectrum['PyTemp'] = parts[6]
  
  spectrum['Source'] = inFile
  
  spectrum['Name']   = ( "S" + spectrum['DB#'] 
                         + ((" RI=" + spectrum['RI']) if 'RI' in spectrum else "")
                         + ((" IS=" + spectrum['IS']) if 'IS' in spectrum else "")
                         + ((" SN=" + spectrum['SN']) if 'SN' in spectrum else "")
                         + " " + spectrum['Sample']
                       )



if __name__ == "__main__":
  main()
