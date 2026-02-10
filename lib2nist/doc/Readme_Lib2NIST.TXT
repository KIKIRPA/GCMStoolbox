May 10, 2017.

This beta-release of Lib2NIST version 1.0.6.5 mass spectral data
conversion program consists of the following files:

Program Files (32-bit)

Lib2NIST.exe         the conversion program
CTNT66b.dll          part of conversion program
zlib1.dll            part of conversion program
libinchi.dll         InChI v.1.05 dll
hptrans.tbl          transliteration table used by Lib2NIST
LICENCE_InChI.pdf    required for libinchi.dll distribution; copied from 
                     http://www.inchi-trust.org/download/105/LICENCE.pdf
_msp_to_peplib_readme.txt short instruction on convering .MSP file to peptide library

Examples and Documentation Files

synon.jdx            JCAMP-DX file example, includes synonyms
synon.MSP            MSP file example, includes synonyms
Textsamp.msp         Compound MSP file example
Strusamp.sdf         SDFile chemical structure example
Strusam2.sdf         Alternate SDFile format
msms_spectrum.MSP    An example of MS/MS spectrum
msms_spectrum.SDF    An example of MS/MS spectrum
Glu-70.MOL           An example of Glycan KCF embedded in molfile
CMDLINE.pdf          Explains Lib2NIST command line options
Readme_Lib2NIST.txt  this file

I. Introduction.
================

The Lib2NIST converter can convert

-- Agilent or HP MS Libraries (with up to 4 structure libraries)
-- NIST MS user libraries
-- Text files in .MSP format optionally with structures in separate molfiles
-- Text files in .SDF format containing both spectra and structures
-- Text files in JCAMP-DX format containing mass spectra (including HP-JCAMP)
-- Text file in .MSP or JCAMP-DX containing mass spectra and associated with
   it file in .SDF format containing chemical structures

into

-- NIST MS user libraries
-- Text files in .MSP format optionally with structures saved in molfiles
-- Text files in HP-JCAMP format (Revision 4.10) recognized by Agilent
   MSD ChemStation
-- Text file in .SDF format containing mass spectra and structures

IMPORTANT: In all input text files, lines must end with 
           Carriage Return/Line Feed characters (CRLF, "\r\n") 

It is possible to convert a subset of spectra, as specified by ID numbers
or CAS registry numbers or NIST registry numbers.

If an input MS/MS spectrum in SDF or MSP file has more peaks than
MS Search can accept, the number of peaks in the output is automatically
reduced by removing the smallest peaks, typically, to 7,000-9,000.
Reducing the max. number of decimal places in peak m/z values, for
example, to 4 with the command line option /PeakMzDecPlaces=4 may
increase the number of peaks saved in the output MS/MS spectrum.
Long peak annotations may significantly reduce the number of peaks.
Typically, peaks and peak annotations of a mass pactrum must fit in 140,000 bytes.

New features in Lib2NIST v.1.0.6.5 build 2017/05/10
=================================================================
Automatic calculation of and indexing by InChIKey
Automatic breaking large MS/MS libraries into parts
Indexing by peaks and losses necessary for
- Any peaks accurate m/z peak search
- Any peaks accurate loss search
- new EI Loss search
- new EI Hybrid search
- new MS/MS Hybrid search

New features in NIST 14 release
=================================================================
New feature: properly converts Glycan KCF embedded in molfile.

New Feature: Building In-source HiRes Search Compatible Libraties
=================================================================
This version builds libraries compatible with the
new In-source HiRes Search introduced in NIST MS Search build 07/05/2013 and later.
To build such a library, turn on "MS/MS Spectra Only" option and either use as input
in-source spectra or use /AccuratePeakMZ command line option.
See file CMDLINE.pdf for more detail.

To add this feature to an old in-source library, rebuild it with Lib2NIST.
In-source HiRes Search Compatible Libraties have files peak_em0.inu and peak_em0.dbu.
To prevent removal of trailing zeroes from m/z values, use command line options
/PrecurMzDecPlaces=keep /PeakMzDecPlaces=keep

As an example, the command line to rebuild NIST 14 MS/MS library may be
Lib2NIST /log8 c:\temp\nist_msms.log c:\temp\nist_msms.ini /outLib c:\nist14\nist_msms =c:\nist17\nist_msms_11 /NoExtra /NoAlias /StdRounding  /MsmsIncNames /IncludeSynonyms:Y /KeepIDs:Y /MwFromFormula:Y /MsmsOnly:Y /Msms2008-Compat:N /UseSubset:N /PrecurMzDecPlaces=keep /PeakMzDecPlaces=keep
(assuming the folder c:\temp exists)
Note: The resultant library will not be searchable by NIST reg.
      numbers, it will not have file
      tree.txt necessary for displaying in MSMS window.
It is always recommended to create and review a log file in case of
mission-critical conversions.

Options
========

The m/z values from text input files can be subject to a specified rounding
transformation, usually to reduce reported m/z to integer (nominal) values.

Deselect "Include synonyms" options to omit chemical name synonyms in
the output

Deselect "Keep IDs unchanged" to make sure the IDs in the newly created
user library are sequential numbers (1, 2, 3,...)

Select "MS/MS spectra only" to process MS/MS spectra.

"2008 MS Search compatible" option
----------------------------------
This option is for backward compatibility only.
It degrades functionality of more recent software. 

Select "2008 MS Search compatible" if you are going to create a
MS/MS library for use with NIST MS Search obtained with NIST 08
MS Library.

Deselect "2008 MS Search compatible" if you are using 04/2010 or later
versions of NIST MSPepSearch available at http://peptide.nist.gov/ 
and/or NIST MS Search from NIST 08 Demo package available at
http://chemdata.nist.gov for mass spectrum searching and displaying.

Select this option when converting a NIST Peptide library into a MSP file
to prevent output of ExactMass and PrecursorMZ lines.

Special case for JCAMP output
 In case of options MS/MS spectra only+2008 MS Search Compatible+Include synonyms,
 JCAMP output has
o version 5.00 instead of 4.10, 
o LDR ##NAMES= contains all synonyms, including $:nn (possibly with hyphes '=')
o Each spectrum ends with ##END=


File Format Notes
=================
For more details on the .MSP file structure see section IV.

For details of the JCAMP-DX file formats see:
P. Lampen, H. Hilling et al, "JCAMP-DX for Mass Spectrometry",
Applied Spectroscopy, 1994, 48 No. 12, 1545-1552, and Web sites
http://www.jcamp-dx.org/
http://wwwchem.uwimona.edu.jm:1104/spectra/testdata/index.html
http://badc.nerc.ac.uk/help/formats/jcamp_dx/
http://www.ualberta.ca/~gjones/jcamp.htm
http://old.iupac.org/jcamp/protocols/dxms01.pdf
etc.

The converter recognizes only (XY..XY) type peak tables.

For details on molfiles and SDFiles see article
A. Dalby, J. G. Nourse et al, J. Chem. Inf. Comput. Sci., 1992,
32, 244-255, and document "CTfile Formats" available at
Accelrys web site (registration may be required)
http://accelrys.com/products/informatics/cheminformatics/ctfile-formats/no-fee.php

Only generic [G] molfile features are recognized by the software.

I.1 User MS Library Limitations
===============================
- Maximum length of a chemical name or a synonym is 511 characters.
- Maximum length of a comment is 1023 characters.
- Maximum length of a mass spectrum is 800 peaks; in case of more
  than 800 peaks, the smallest peaks will be ignored by the Lib2NIST
  to reduce the spectrum length to 800 peaks.
- Maximum chemical formula length is 23 characters.
- Maximum number of spectra in the ordinary user library is 65,535.
- Maximum ID value of a spectrum in the ordinary user library is
  65,535; IDs start from 1.
- Maximum molecular mass is 2000.
- Maximum MS peak mass number indexed for the Default user spectrum
  presearch or Any Peak search is 2000.
- Maximum user library record length is 5000 bytes; if the spectrum
  does not fit then as many last synonyms as necessary to reduce the
  record length to 5000 are ignored.

MS/MS Library features

- Maximum number of spectra may exceed 65535
- Maximum comment length is 2047 bytes
- Peaks are also saved and indexed for fast mass spectrum searching
  with accurate m/z values and intensities, and may have text
  annotations. Number of peaks saved in this format may exceed 800.
- Maximum molecular weight, peak m/z, and precursor m/z values may
  exceed 2000. 
- MS/MS libraries created by Lib2NIST may not be altered by the
  NIST MS Search program.

II. Import/Export of Synonyms.
==============================
Files SYNON.MSP and SYNON.JDX are examples of the converter
input files to illustrate how compound name synonyms can be
added to the user mass spectral library.

Synonyms in the user libraries are supported by NIST MS Search
Program starting from version 1.7.

To export synonyms to NIST user library or .MSP format make
sure the "Include Synonyms" option is selected.

Starting with Lib2NIST version  1.0.4, synonyms may be exported to
a HP-JCAMP file. The format is different from that in SYNON.JDX.
A 4-character string " $$ " is used as a delimiter. The total length
of the names string which follows LDR ##CAS_NAME= cannot be greater
than 511 characters.


III. Import of Structures from molfiles.
========================================

Molecular structures located in separate molfiles can be
associated with the spectra located in a single .MSP file
and converted into the user library or (starting from Lib2NIST
v. 1.0.4) into a SDfile.

To achieve this the molfiles should have predefined names
and be located in the folder with same name as the name of
the input .MSP file and extension .MOL.

III.A. molfile names
----------------------
To associate a molfile with a compound having, for example,
CAS reg. number 50555, the molfile should have name
s50555.mol

To associate a molfile with a compound having, for example, ID=15
(15 is either an ordering number of the spectrum in the .MSP
file or the spectrum in the .MSP file has line "ID: 15" or
a spectrum in the input library has ID = 15), the molfile
should have the name id15.mol

Optionally, a molfile may be associated with a NIST number. For
NIST number=1234, the molfile name is N1234.MOL. To enable
this feature, start Lib2NIST with command line option
/MspLinkedByNISTrn

III.B. molfiles location.
-------------------------
The folder containing molfiles should be located in the
folder where .MSP file is. For example, if .MSP file is
C:\NIST11\mssearch\MYSPECS.MSP
then the folder with molfiles MUST be
C:\NIST11\mssearch\MYSPECS.MOL
and contain files like
C:\NIST11\mssearch\MYSPECS.MOL\s50555.mol
C:\NIST11\mssearch\MYSPECS.MOL\id15.mol

When converting any .MSP file, the converter always looks
for a folder with a name derived from the name of the
.MSP file. In case when 2 molfiles are associated with
the particular spectrum (one by CAS reg. number, another
by ID) the converter ignores the former and picks up the
latter molfile.  If association with the NIST number option
is used then the molfile associated with the NIST number,
if exists, has the highest precedence.

The names and locations described above are exactly the same
as those the converter would produce when converting to
a text file in .MSP format with structures saved in molfiles.

When converting a library or SDfile into an MSP file with
Output Format "Text File (.MSP) + MOLfiles linked by BOTH",
if a spectrum has CAS r.n., then a molfile associated with
the CAS r.n. is created, otherwise a molfile associated with
the ID is created.

IV. Other examples.
===================
Files TEXTSAMP.MSP and STRUSAMP.SDF are sample input text
files for the Lib2NIST converter. They represent two of
the text file types recognized by the present version of
the Lib2NIST library converter.

TEXTSAMP.MSP is self-explanatory. In addition to a mass
spectrum and a name, this kind of file may contain
a CAS rn, a formula, and a nominal molecular weight.

Please note the STRUSAMP.SDF format is rather strict.
It contains molfiles, each followed by a mass spectrum.
A record for each compound is made out of 5 parts, the
first of them (structure) being optional:

1) Chemical structure in MOLfile format (may have no atoms or bonds)

If present, the first line (name) and the third line (comment)
will be replaced before saving molfile into the NIST User MS
library. Aromatic bonds may be only in even-member rings.

If molfile contains aromatic bonds (type=4), the converter
will transform them into alternate single/double bonds and
completely change the whole molfile before saving it into
the NIST User MS library. Aromatic bonds in rings containing
odd number of atoms cannot be properly converted to
alternate single/double bonds.

2) One line separating molfile from mass spectral data part:
> <MASS SPECTRUM>

3) Mass spectrum in ASCII form, same as in TEXTSAMP.MSP
It cannot have blank lines.

4) One blank line

5) One line marking the end of the record for the compound:
$$$$

Please note there are no blank lines between "$$$$" line and
the first line of the next record.

STRUSAM2.SDF was created by Lib2NIST from STRUSAMP.SDF. It is
an example of an alternate SDF file format. This format is
also recognized by the Lib2NIST.

msms_spectrum.MSP and msms_spectrum.SDF are examples of MSP and SDfile
containg MS/MS spectra. A MS/MS spectrum file must have precursor m/z value.
Examples of MSP files containing peptide MS/MS spectra may be found here:
http://peptide.nist.gov
This site uses term "Library" for MSP files.

