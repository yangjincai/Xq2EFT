#!/usr/bin/python
#
#This codes is to convert cartesian molecular coordinates 
#    from one format to another.
#                                       zhao.lf@gmail.com
#
#  The coordinate structure of intermediate data is:
#      [[elem, x, y, z],
#       [elem, x, y, z],
#       ...]
#
#  1. simple input syntax allowed.            1.52  2011.07.12
#  

__version__ = "1.52"
__revision__ = """  1. read unfinished nwchem opt files.\n"""
__doc__ = """\n  Molecular coordinates format transferor. --Lifeng Zhao\n
"""

import sys
import os
import string
import inspect
from copy import deepcopy

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

GAMESS_Settings = """ $CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE MPLEVL=2 $END
-$CONTRL ICHARG=1 $END
 $SYSTEM MWORDS=100 MEMDDI=1000 $END
-$CONTRL EXETYP=CHECK $END
 $CONTRL MAXIT=200 $END
-$STATPT OPTTOL=1.0E-5 $END
 $STATPT NSTEP=300 $END
-$DFT DC=.T. $END
 $SCF DIRSCF=.T. $END
 $BASIS GBASIS=N311 NGAUSS=6 NDFUNC=2 NPFUNC=2 DIFFSP=.T. DIFFS=.T. $END
 $GUESS GUESS=HUCKEL $END
-$ELPOT IEPOT=1 WHERE=PDC $END
-$PDC PTSEL=GEODESIC $END
-CONSTR=QUPOLE $END
 $DATA
--Cartesian coordinates with C1 symmetry as follows:
C1
"""

ZCharge = {'O':'8.0','N':'7.0',\
           'C':'6.0','H':'1.0',\
           'B':'5.0','F':'9.0',\
           'Na':'11.0','NA':'11.0',\
           'P':'15.0','S':'16.0',\
           'Cl':'17.0','CL':'17.0',\
           'Br':'35.0','BR':'35.0',\
           'CU':'29.0','RU':'44.0',\
           'AU':'79.0','Au':'79.0','Se':'34.0'}

ELEMENT = ['X','H','He','Li','Be','B','C','N','O','F','Ne',\
           'Na','Mg','Al','Si','P','S','Cl','Ar','K','Ca',\
           'Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn',\
           'Ga','Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr',\
           'Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn',\
           'Sb','Te','I','Xe','Cs','Ba',\
           'La','Ce','Pr','Nb','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu',\
           'Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn']

SpecialData = {'TotalCharge':0,
		'Multiplicity':1,
		'InputFileName':'',
		'OutputFileName':'',
		'Energy':0.0}

def ReadXYZ(CoordFile):
    coordtemp = []

    NumAtoms = CoordFile.readline()
    NumAtoms = int(NumAtoms.split()[0])

    for ii in range(NumAtoms):
        line = CoordFile.readline()
    line = CoordFile.readline()
    CoordFile.seek(0)
    if line.strip()!='':
        sys.stdout.write('  This file seems a general xyz file.\n')
        line = CoordFile.readline()
        line = CoordFile.readline()
        for ii in range(NumAtoms):
            line = CoordFile.readline()
            line = line.strip()
            line = line.split()
            coordtemp.append(line[0:4])
    else:
        sys.stdout.write('  This file seems a TINKER xyz file.\n')
        line = CoordFile.readline()
        for ii in range(NumAtoms):
            line = CoordFile.readline()
            line = line.strip()
            line = line.split()
            coordtemp.append(line[1:5])
     
    return coordtemp


def ReadGJF(CoordFile):
    coordtemp = []
    while 1:
        line = CoordFile.readline()
        if line[0] == '#': break
        if line == '':
            print 'Error: wrong gjf or com format! \n',lineno()
            coordtemp.append('Error')
    if not(len(coordtemp) == 0): return 2
    
    line = CoordFile.readline()
    while 1:
        if line.strip() != '': line = CoordFile.readline()
        else: break
    for ii in range(3): CoordFile.readline()
    
    while 1:
        line = CoordFile.readline()
        if line.strip() == '': break
        line = line.split()
        if len(line)<4:
            print "CAUTION: It seems that the .gjf file was writen in Z-Matrix format,"
            print "        try to convert it to cartesian format.",lineno()
            return 3
        if len(line)>5: coordtemp.append([line[0], line[2], line[3], line[4]])
        else: coordtemp.append(line[:4])
        
    return coordtemp

def ReadINP(CoordFile):
    coordtemp = []
    while 1:
        line = CoordFile.readline()
        if (line[1:6]=='$DATA') or (line[1:6]=='$data'): break
        if line == '': return 4

    CoordFile.readline()    
    line = CoordFile.readline()
    if (len(line)<2) or (line.strip() != 'C1'):
        print "Wrong .inp file format! This codes can only deal C1 symmetry!",lineno()
        return 5
    
    while 1:
        line = CoordFile.readline()
        line = line.split()
        if (len(line)==0) or (line[0]=='$END') or (line[0]=='$end'): break
        line.pop(1)
        coordtemp.append(line)
    return coordtemp


#---Lan, output two lists:[element,zcharge] and [x,y,z]
def ReadINPfull(CoordFile):
    coordtemp = []
    zelems = []
    while 1:
        line = CoordFile.readline()
        if (line[1:6]=='$DATA') or (line[1:6]=='$data'): break
        if line == '': return 4

    CoordFile.readline()
    line = CoordFile.readline()
    if (len(line)<2) or (line.strip() != 'C1'):
        print "Wrong .inp file format! This codes can only deal C1 symmetry!",lineno()
        return 5

    while 1:
        line = CoordFile.readline()
        line = line.split()
        if (len(line)==0) or (line[0]=='$END') or (line[0]=='$end'): break
        if (len(line)!=5): sys.exit(1)
        zelems.append(line[:2])
        coordtemp.append(line[2:])
    return (zelems,coordtemp)
    

def ReadPDB(CoordFile):
    coordtemp = []
    while 1:
        line = CoordFile.readline()
        if len(line)>=4:
            if line[0:4]=='ATOM' or line[0:6]=='HETATM':
                #element = line[12:16]
                #element = element.strip()
                #if element=='HC' or element=='HO' or element=='HN': element = 'H'
                #if ord(element[0])<58: element = element[1]
		element = line[76:78]
		element = element.strip()
                xx = line[30:38]
                xx = xx.strip()
                yy = line[38:46]
                yy = yy.strip()
                zz = line[46:54]
                zz = zz.strip()
                coordtemp.append([element, xx, yy, zz])
        if line == '': break

    return coordtemp


def ReadNWinp(CoordFile):
    coordtemp = []

    while 1:
        line = CoordFile.readline()
        if line == '': break

        if len(line)>8 and line.split()[0].upper()=='GEOMETRY':
            while 1:
                line = CoordFile.readline()
                if line.strip().upper()=='END': break

                if line.strip()!='':
                    line = line.split()
                    coordtemp.append(line)

            break

    return coordtemp

 
def ReadLOG(CoordFile):
    filetype = ''
    while 1:
        line = CoordFile.readline()
        if 'GAMESS VERSION' in line:
            filetype = 'gms'
            break
        elif 'Gaussian, Inc.' in line:
            filetype = 'gau'
            break
        elif 'NWChem' in line:
            filetype = 'nw'
            break

        if line == '': break

    if   filetype == 'gms': coordtemp = ReadGMS(CoordFile)
    elif filetype == 'gau': coordtemp = ReadGAU(CoordFile)
    elif filetype == 'nw' : coordtemp = ReadNWChem(CoordFile)
    else: 
        print 'Wrong log file format! Exit!',lineno()
        return 7

    return coordtemp

def ReadGMS(CoordFile):
    print '\nGamess file,',
    CoordFile.seek(0)
    coordtemp =[]

    runtyp = ''
    while 1:
        line = CoordFile.readline()
        if line=='': break

        #if len(line)>=11 and line[:11]==' INPUT CARD':
        if line.find('$CONTRL OPTIONS')>-1:
            line = CoordFile.readline()
            while 1:
                line = CoordFile.readline()
                if line.strip()=='': break
                if line.find('RUNTYP')>-1:
                    line = line.split()
                    for wd in line:
                        temp = wd.split('=')
                        if temp[0]=='RUNTYP':
                            runtyp=temp[1]
                            break
                    break

    CoordFile.seek(0)
    if runtyp == 'OPTIMIZE':
        print 'OPT job,',
        while 1:
            line = CoordFile.readline()
            if 'EQUILIBRIUM GEOMETRY LOCATED' in line:
                print 'EQUILIBRIUM GEOMETRY LOCATED'
                break
            if line=='':
                print 'BUT equilibrium geometry NOT found! The last frame dumped.',lineno()
                break

    # Begin read coord:
    CoordFile.seek(0)
    while 1:
        line = CoordFile.readline()
        if line == '': break

        if line.strip()=='COORDINATES OF ALL ATOMS ARE (ANGS)':
            # Found a coord:
            coordtemp = []
            for ii in range(2): CoordFile.readline()

            while 1:
                line = CoordFile.readline()
                if line.strip()=='': break

                line = line.split()
                line.pop(1)
                coordtemp.append(line)
                    
    if coordtemp==[]:
        CoordFile.seek(0)
        IsFound = False
        while 1:
            line = CoordFile.readline()
            if line=='':
                sys.stderr.write('No coordinates found.\n')
                return 9

            if line.upper().find('INPUT CARD> $DATA')>-1:
                CoordFile.readline()
                CoordFile.readline()
                while 1:
                    line = CoordFile.readline()
                    if line.upper().find('INPUT CARD> $END')>-1:
                        IsFound = True
                        break
                    line = line[12:]
                    line = line.split()
                    line.pop(1)
                    coordtemp.append(line)
            if IsFound:
                sys.stdout.write('Coordinates converted from GAMESS input stream.\n')
                return coordtemp

    else:             return coordtemp

def ReadGAU(CoordFile):
    global SpecialData
    print '\nGaussian job, end coordinations read.'
    CoordFile.seek(0)

    runtyp = ''
    while 1:
        line = CoordFile.readline()
        if line=='':
            raise Exception, "No coordinates found!"

        if len(line)>2 and line[1]=='#':
            if 'opt' in line:
                runtyp = 'opt'
            else:
                line = CoordFile.readline()
                if 'opt' in line:
                    runtyp = 'opt'

        if line.find('Charge')>-1 and line.find('Multiplicity')>-1:
            line = line.split()
            SpecialData['TotalCharge'] = int(line[2])
            SpecialData['Multiplicity'] = int(line[5])
            break

    StrangeElement = False
    #if runtyp = 'opt':
    #    print 'Gaussian optimization job.'

    while 1:
        line = CoordFile.readline()
        if line == '': break

        if ('Input orientation:' in line) or ('Standard orientation:' in line):
            coordtemp = []
            for ii in range(4): line = CoordFile.readline()

            ## Locate coords for current config:
            while 1:
                line = CoordFile.readline()
                if len(line)>9 and line[:10]==' ---------': break

                line = line.split()
                ndx = int(line[1])
                if ndx > len(ELEMENT):
                    StrangeElement = True
                    ndx = str(ndx)
                else: ndx = ELEMENT[ndx]
                coordtemp.append([ndx,line[3],line[4],line[5]])

            ## Locate energy value for current config:
            while 1:
                line = CoordFile.readline()
                if line=='':
                    break

                if line.find('SCF Done:')>-1:
                    line = line.split('=')[1]
                    line = line.split()
                    SpecialData['Energy'] = float(line[0])
                    break

    if StrangeElement:
        print "\n###################################################################"
        print "!!!Warning: There are special elements with no symbol assigned!!!"
        print "###################################################################"

    return coordtemp    


def ReadNWChem(CoordFile):
    sys.stderr.write('\n  NWChem job, end coordinations read.\n')
    CoordFile.seek(0)

    runtyp = ''
    while 1:
        line = CoordFile.readline()
        if   line == '': break
        elif line.strip() == 'NWChem Geometry Optimization':
            runtyp = 'opt'
            break

    if runtyp == '':
        print '\nNot an optimization job, exit.',lineno()
        return 100
    else:
        IsOpted = False
        CoordFile.seek(0)
        coordtemp = []
        coordtempbackup = []
        while 1:
            line = CoordFile.readline()
            if line == '': break

            templine = line.split()
            if len(templine)==2 and templine[0]=='Step':
                coordtempbackup = []
                while 1:
                    line = CoordFile.readline()
                    line = line.strip()
                    if line.find('No.')==0: break
                line = CoordFile.readline()
                while 1:
                    line = CoordFile.readline()
                    if line.strip()=='': break
                    line = line.split()
                    line.pop(0)
                    line.pop(1)
                    coordtempbackup.append(line)
                coordtemp = deepcopy(coordtempbackup)
            if line.strip() == 'Optimization converged':
                IsOpted = True
                coordtemp = []
                while 1:
                    line = CoordFile.readline()
                    if line.strip() == 'Geometry "geometry" -> "geometry"':
                        for ii in range(6): CoordFile.readline()
                        while 1:
                            line = CoordFile.readline()
                            if line.strip()=='': break

                            line = line.split()
                            line.pop(0)
                            line.pop(1)

                            coordtemp.append(line)

                        break
                break
    if IsOpted: sys.stderr.write('  Optimization converged.\n')
    else:       sys.stderr.write('  Optimization NOT converged, last configuration read.\n')
                           
    return coordtemp


def ReadREBO(CoordFile):
    coordtemp = []

    while 1:
        line = CoordFile.readline()
        if line == '': break

        line = line.split()
        if (len(line)>1) and (line[1].lower()=='atoms'):
            Natoms = int(line[0])

        if len(line)>0 and line[0].lower() == 'atoms':
            CoordFile.readline()
            for ii in xrange(Natoms):
                line = CoordFile.readline()
                line = line.split()
                if line[1]=='1': elem = 'C'
                else: elem = 'H'
                coordtemp.append([elem, line[2], line[3], line[4]])

    return coordtemp

#def ReadARC(CoordFile, PDBFile):

def ReadGRO(CoordFile):
    return 6


################## Writing procedures ##########################
def WriteXYZ(file_h, coords):
    file_h.write("%d\nAtoms\n" % len(coords))
    for atom in coords:
        file_h.write("%2s" % atom[0])
        for ii in range(1,4):
            file_h.write("%15s" % atom[ii])
        file_h.write("\n")
    file_h.write("\n")
    return
    
def WriteGJF(file_h, coords):
    prefix = os.path.splitext(SpecialData['OutputFileName'])[0]
    file_h.write("%%chk=%s.chk\n%%mem=500MW\n%%nprocshared=8\n"%prefix)
    file_h.write("# B3LYP/6-31g(d)\n\n")
    file_h.write('From "%s"'%SpecialData['InputFileName'])
    if SpecialData==0.0: pass
    else:
        file_h.write(' E: %12.8f'%SpecialData['Energy'])
    file_h.write('\n\n')
    file_h.write("%d %d\n"%\
                 (SpecialData['TotalCharge'], SpecialData['Multiplicity']))
    for atom in coords:
        file_h.write("%2s" % atom[0])
        for ii in range(1,4):
            file_h.write("%18s" % atom[ii])
        file_h.write("\n")
    file_h.write("\n")
    return
    
def WriteINP(file_h, coords):
    file_h.write("! Gamess input file generated by mol2mol.\n")
    file_h.write(GAMESS_Settings)
    for atom in coords:
        file_h.write("%2s" % atom[0])
        if atom[0].upper() in ZCharge: 
            file_h.write("%8s" % ZCharge[atom[0].upper()])
        else:
            file_h.write("%8s" % "X")  # if the element is unknown print 'X'.
            print "\n###################################################################"
            print "!!!Warning: There are special elements with no atom No. assigned!!!"
            print "###################################################################"
        for ii in range(1,4): file_h.write("%15s" % atom[ii])
        file_h.write("\n")
    file_h.write(" $END\n")    
    return

def WritePDB(file_h, coords, IsWrtTitle=True, NdxAtom=1, NameRes='LIG', NdxRes=1):
    if IsWrtTitle:
        file_h.write('TITLE     THIS PDB FILE IS GENERATED BY "mol2mol" --lfzhao.\n')
    for atom in coords:
        file_h.write("ATOM  %5d%3s%6s A%4d%12.3f%8.3f%8.3f  1.00  0.00\n" % (NdxAtom,atom[0], NameRes, NdxRes,float(atom[1]),float(atom[2]),float(atom[3])))
        NdxAtom += 1
    return
    

def WriteNWinp(file_h, coords):
    file_h.write('Title "NWChem input file generated by mol2mol. --L. Zhao"\n\n')
    file_h.write('echo\nstart\n\nmemory 2000 mb\n\n')
    file_h.write('geometry units angstroms\n')
    for atom in coords:
        file_h.write('%2s' % atom[0])
        for ii in range(1,4):
            file_h.write('%18s' % atom[ii])
        file_h.write('\n')

    file_h.write('end\n\nbasis\n  * library 6-31g*\nend\n\nscf direct; end\n\n')
    file_h.write('dft\n  xc b3lyp\n  iterations 300\nend\n\ntask dft optimize')
    return


def WriteAIREBO(file_h, coords):
    file_h.write('# This file is for McRebo program. Generated by "mol2mol" - lfzhao\n\n')
    Ntemp = len(coords)
    file_h.write('%5d  atoms\n\n' % Ntemp)
    file_h.write('2 atom types\n\n')
    file_h.write('0.0  30.0  xlo xhi\n')
    file_h.write('0.0  30.0  ylo yhi\n')
    file_h.write('0.0  30.0  zlo zhi\n\n')
    file_h.write('Masses\n\n    1    12.01100    # C\n    2     1.00794    # H\n\n')
    file_h.write('Atoms\n\n')
    for ii in range(Ntemp):
        if   coords[ii][0]=='C': Ttemp = 1
        elif coords[ii][0]=='H': Ttemp = 2
        else:
            sys.stderr.write('  Error: atom name is not "C" or "H"\n\n')
            sys.exit()
            
        file_h.write('%6d  %6d       %8s %8s %8s\n' % \
                     (ii+1, Ttemp, coords[ii][1], coords[ii][2], coords[ii][3]))
    sys.stderr.write("\n###################################################################\n")
    sys.stderr.write("!!!  CAUTION: Default box size used (30 Angstrom).                 \n")
    sys.stderr.write("###################################################################\n")

    return

def WriteGRO(file_h, coords):
    return
    
def NW2GMS(file1,file2):

    ## Locate file head of frequency calculation:
    while 1:
        line = file1.readline()
        if line == '':
            print 'Error in reading file.',lineno()
            sys.exit(1)

        if line.strip()=='NWChem Nuclear Hessian and Frequency Analysis':
            for ii in range(5): line = file1.readline()

            if 'Analytic' in line:
                print '\nAnalytic Hessian Calculation.'
            elif 'Finite-difference' in line:
                print '\nNumerical Hessian Calculation.'
            else: print '\nUnknown Type Hessian Calculation :('

            break

    ## Find Energy:
    while 1:
        line = file1.readline()
        if line == '':
            print '\nError in reading file. Line %d\n' % lineno()
            sys.exit(1)

        if 'Total DFT energy =' in line:
            print '\nDFT calculations.'
            line = line.split()
            Energy = float(line[-1])
            break
        elif 'Total MP2 energy' in line:
            print '\nMP2 calculations.'
            line = line.split()
            Energy = float(line[-1])
            break

    ## Locate atomic coordinates:
    while 1:
        line = file1.readline()
        if line == '':
            print '\nError in reading file. Line %d\n' % lineno()
            sys.exit(1)

        if 'Atom information' in line: break

    file1.readline()
    file1.readline()

    ## Read atomic coordinates:
    temp_coord = []
    while 1:
        line = file1.readline()
        if line[1:11]=='----------': break

        line = line.split()
        for ii in range(2,5): line[ii] = float(line[ii].replace('D','E'))
        temp_coord.append(line)

    NumOfAtoms = len(temp_coord)
    dim = 3*NumOfAtoms
    freqs = []
    dxyz = []
    for ii in range(dim): dxyz.append([])

    ## Locate & read freqencies values:
    OK = False
    while 1:
        line = file1.readline()
        if 'Projected Frequencies expressed in cm-1' in line:
            while 1:
                for ii in range(3): file1.readline()
                line = file1.readline()
                line = line.split()
                for ii in line[1:]: freqs.append(float(ii))

                file1.readline()
                for ii in range(dim):
                    line = file1.readline()
                    line = line.split()
                    for jj in line[1:]: dxyz[ii].append(float(jj))

                if len(dxyz[0])>=dim:
                    OK = True
                    break

        if OK: break

    ## Locate & read freqencies intensities:
    intensities = []
    while 1:
        line = file1.readline()
        if 'Projected Infra Red Intensities' in line:
            file1.readline()
            file1.readline()

            for ii in range(dim):
                line  = file1.readline()
                line = line.split()
                intensities.append(float(line[4]))

            break

    # Write Gamess log file.
    file2.write("""          ******************************************************
          *         GAMESS VERSION = 11 APR 2008 (R1)          *
          *             FROM IOWA STATE UNIVERSITY             *
          * M.W.SCHMIDT, K.K.BALDRIDGE, J.A.BOATZ, S.T.ELBERT, *
          *   M.S.GORDON, J.H.JENSEN, S.KOSEKI, N.MATSUNAGA,   *
          *          K.A.NGUYEN, S.J.SU, T.L.WINDUS,           *
          *       TOGETHER WITH M.DUPUIS, J.A.MONTGOMERY       *
          *         J.COMPUT.CHEM.  14, 1347-1363(1993)        *
          **************** 64 BIT INTEL VERSION ****************

 THE POINT GROUP OF THE MOLECULE IS C1
 THE ORDER OF THE PRINCIPAL AXIS IS     0

 ATOM      ATOMIC                      COORDINATES (BOHR)
           CHARGE         X                   Y                   Z
""")
    
    for atom in temp_coord[:]:
        file2.write('%2s%14s%17.10f%20.10f%20.10f\n' % (atom[0],ZCharge[atom[0]],atom[2],atom[3],atom[4]))

    file2.write("""\n     $CONTRL OPTIONS
     ---------------
 SCFTYP=RHF          RUNTYP=HESSIAN      EXETYP=RUN

 FINAL R-B3LYP1 ENERGY IS%20.10f AFTER  11 ITERATIONS

     FREQUENCIES IN CM**-1, IR INTENSITIES IN DEBYE**2/AMU-ANGSTROM**2,
     REDUCED MASSES IN AMU.

          --------------------------------------------------------
          NORMAL COORDINATE ANALYSIS IN THE HARMONIC APPROXIMATION
          --------------------------------------------------------
""" % Energy)

    ndx = 0
    OK = False
    while 1:
        ndx_begin = ndx*5
        ndx_end   = (ndx+1)*5
        if ndx_end >= dim:
            ndx_end = dim
            OK = True

        file2.write('\n               ')
        for ii in range(ndx_begin,ndx_end): file2.write('%12d' % (ii+1))
        file2.write('\n       FREQUENCY: ')
        for ii in range(ndx_begin,ndx_end): file2.write('%12.2f' % (freqs[ii]))
        file2.write('\n    IR INTENSITY: ')
        for ii in range(ndx_begin,ndx_end): file2.write('%12.5f' % (intensities[ii]))
        file2.write('\n')

        for ii in range(dim):
            temp_ndx0 = int(ii+1)/3
            temp_ndx1 = (ii+1)%3
            if   temp_ndx1 == 1: file2.write('\n%3d%4s            X' % (temp_ndx0+1,temp_coord[temp_ndx0-1][0]))
            elif temp_ndx1 == 2: file2.write('\n                   Y')
            elif temp_ndx1 == 0: file2.write('\n                   Z')
            for jj in range(ndx_begin,ndx_end): file2.write('%12.8f' % dxyz[ii][jj])

        file2.write('\n')

        if OK: break
        ndx = ndx + 1 

    return


def Translate(IFileName, OFileName, params={}):
    file1type = os.path.splitext(IFileName)
    file2type = os.path.splitext(OFileName)
    file1type = file1type[1]
    file2type = file2type[1]

    Ifile = open(IFileName, 'r')
    Ofile = open(OFileName, 'w')

    if params['-n2g']:
        NW2GMS(Ifile, Ofile)
        Ifile.close()
        Ofile.close()
        sys.stderr.write('\n  Done.\n\n')
        sys.exit(0)

    if params['-pdb']:
        PDBFile = open(params['-pdb'],'r')
        CoordAll = ReadARC()
        PDBFile.close()
        sys.exit()

    CoordFile = Ifile
    if   file1type == '.xyz': Coordtemp = ReadXYZ(CoordFile)
    elif (file1type == '.gjf') \
        or (file1type == '.com'): Coordtemp = ReadGJF(CoordFile)
    elif file1type == '.pdb': Coordtemp = ReadPDB(CoordFile)
    elif file1type == '.inp': Coordtemp = ReadINP(CoordFile)
    elif file1type == '.log': Coordtemp = ReadLOG(CoordFile)
    elif file1type == '.nwo': Coordtemp = ReadLOG(CoordFile)
    elif file1type == '.nw' : Coordtemp = ReadNWinp(CoordFile)
    elif file1type == '.data': Coordtemp = ReadREBO(CoordFile)
    else: Coordtemp = ReadGRO(CoordFile)
    if isinstance(Coordtemp, int):
        sys.stderr.write('\n  Failed!(%d)\n\n' %Coordtemp)
        sys.exit(1)

    coords = Coordtemp
    if   file2type == '.xyz': WriteXYZ(Ofile, coords)
    elif (file2type == '.gjf') \
        or (file2type == '.com'): WriteGJF(Ofile, coords)
    elif file2type == '.pdb': WritePDB(Ofile, coords)
    elif file2type == '.inp': WriteINP(Ofile, coords)
    elif file2type == '.nw':  WriteNWinp(Ofile, coords)
    elif file2type == '.data': WriteAIREBO(Ofile, coords)
    else: WriteGRO(file2, coords)

    Ifile.close()
    Ofile.close()
    return

    
def ReadArgs():
    usage = """  Usage: -f   string : Input file name;
           -o   string : Output file name;
           -n2t (optional)boolean  Only for Translation from nwchem FREQUENCIES to gamess format
           -pdb (optional)string   Only for Translation from Tinker arc/xyz to pdb format

  File formats allowed currently:
      GAUSSIAN:   (input) .gjf, .com
      GAMESS-US:  (input) .inp
                  (output).log
      TINKER:     (input) .xyz
      PDB:        .pdb
      NWCHEM:     (input) .nw
                  (output).nwo

  Please report bugs to <zhao.lf@gmail.com>\n\n"""

    argv_err = """  Arguments error! Try "-h".\n"""

    options = {'-f':'','-o':'','-pdb':''}
    optionsYN = {'-n2g':False}

    sys.stderr.write(__doc__)

    num_argvs = len(sys.argv)
    ## No other arguments:
    if   num_argvs==1:
        sys.stderr.write(usage)
        sys.exit(1)
    ## Only one argument:
    elif num_argvs==2:
        if sys.argv[1]=='-h' or sys.argv[1]=='--help':
            sys.stdout.write(usage)
            sys.exit(0)
        else:
            sys.stderr.write(argv_err)
            sys.exit(1)
    ## Simple input format:
    elif num_argvs==3:
        options['-f'] = sys.argv[1]
        options['-o'] = sys.argv[2]
        options['-n2g'] = False
        options['-pdb'] = False
        return options
    ## More than one:
    else:
        ndx = 1
        while 1:
            if sys.argv[ndx] in options:
                #if ndx==num_argvs-1: break
                #else:
                    options[sys.argv[ndx]] = sys.argv[ndx+1]
                    ndx += 2
            elif sys.argv[ndx] in optionsYN:
                if (ndx+1)>=num_argvs or sys.argv[ndx+1][0] == '-':
                    optionsYN[sys.argv[ndx]] = True
                    ndx += 1
                elif sys.argv[ndx+1].upper() in ['Y','YES','T','TRUE']:
                    optionsYN[sys.argv[ndx]] = True
                    ndx += 2
                else:
                    ndx += 2
            else:
                sys.stderr.write(argv_err)
                sys.exit(1)
            if ndx >= num_argvs: break

    for ii in optionsYN.keys(): options[ii]=optionsYN[ii]
    return options



if __name__ == '__main__':
    options = ReadArgs()

    file1name = options['-f']
    file2name = options['-o']

    SpecialData['InputFileName'] = file1name
    SpecialData['OutputFileName'] = file2name

    params = {}
    params['-n2g'] = options['-n2g']
    params['-pdb'] = options['-pdb']

    ## TRANSLATE:
    Translate(file1name, file2name, params)

    sys.stderr.write('\n  Done.\n\n')
    sys.exit(0)

