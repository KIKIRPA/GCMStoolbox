To convert a single msp file (typically, *_consensus_final_true_lib.msp)
to a peptide library, run

Lib2NIST.exe /msp2peplib

This starts conversion with running ShortenPeplibComments.exe code incorporated in Lib2NIST.
This is the preferred way of creating NIST Peptide Library
This option implies /IncludeSynonyms:Y /KeepIDs:N /MwFromFormula:N /MsmsOnly:Y /Msms2008-Compat:N /UseSubset:N /Z /NOEXTRA /StdRounding /OutLib

IMPORTANT: *Do not use this method to run 2 or more instances of Lib2NIST concurrently*

The old script _convert_msp_to_msmslib.bat should not be used because ShortenPeplibComments.exe
has not been updated.

To create peptide-specific incremental names, add option /PepIncNames
Other useful options (see CMDLINE.pdf for more information):
/NoExtra /NoAlias /PrecurMzDecPlaces=keep /PeakMzDecPlaces=keep 
