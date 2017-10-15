#!/usr/bin/env python
#! -*- coding: utf-8 -*-

'''
Matrix-determinant beregning af beam m point loads.
Data og resultater in/out til .txt fil.
Bytecode via python shell i cwd:
>>> import py_compile
>>> py_compile.compile('fobm5.py')
-genererer fobm5.pyc ved siden af .py

'''

import numpy as np
from numpy import linalg as LA
import os
import sys
import textool
import subprocess


if sys.platform.startswith( 'win'):
    def clear_screen():
        subprocess.call([ "cmd.exe", "/C", "cls" ])
else:
    def clear_screen():
        subprocess.call([ "clear" ])

def InsPlace( mtrix, lst):
    # lst (list) inserted in matrix (list-of-lists), sorted by 'lst[0]'
    if len( mtrix):     # hvis nogen i forvejen
        if lst[0] > mtrix[-1][0]:   # if nye pos > pos i sidste matrix-list
            mtrix.append( lst)      # saa append og slut
        else:
            indx=0                  # line[0] skal ind inden sidste elin[0]
            for elin in mtrix:
                if abs( lst[0] - mtrix[indx][0]) < 0.01:  # ca lig med
                    mtrix[indx][1] =lst[1]    # saa ret val ved denne x           
                    break
                elif lst[0] < mtrix[indx][0]:   # 1. gang mindre end exist
                    mtrix.insert( indx, lst)    # saa indset her
                    break
                indx +=1             # ellers fortset for-loop
    else:               # ellers ingen i forvejen
        mtrix.append( lst)
    return mtrix

def alfa( end, a, b):
    # influence coefficient = return-value /6K,  K=EI/L^3
    # alfa(x,x)/6K = 1/k(x)
    # a, b dist from left in frac of L, for pnt-masses Ma og Mb
    # 'end' er enten 'cf', 'hh', 'ch' eller 'cc'
    if b < a:
        c= a
        a= b
        b= c
    if end == 'cf':
        return a**2 *(3*b-a)
    elif end == 'hh':
        return (1-b)*a*( b*(2-b)-a**2 )
    elif end == 'ch':
        return (1-b)*a**2*( 3*(1-a)+(a-3)*(1-b)**2 ) /2.0
    elif end == 'cc':
        return (1-b)**2*a**2*( 3*b-a*(1+2*b) )

def lofrq( econ, pmlst):
    # return verdi skal ganges med K=EI/L³ for at give omega² for laveste efrekv
    # econ, end-conditions er 'cf', 'hh', 'ch' or 'cc'
    # pmlst er point mass list.
    dim= len(pmlst)
    ary= []
    row= 0
    while row < dim:
        arow= []
        col= 0
        while col < dim:
            arow.append( pmlst[col][1]* alfa( econ, pmlst[row][0],pmlst[col][0] ) )
            col+=1
        ary.append( arow)
        row+=1
    e_vals= LA.eigvals(ary)
    e_vals.sort()
    return [6.0/e_vals[-1], 6.0/e_vals[-2]]     # return * K = omega^2

def Beam( end, xpos, ind):
    # Returnerer en list med tre strenge der skal printes over hinanden
    # Giver tegning af beam med pkt-M(er) ca paa plads.
    # 'end' er cf, hh ch eller cc 
    # 'xpos' er float frac of L, 0 - 1 
    # 'ind' er indent space-string
    p=0
    xnum=[]
    nx=len(xpos)
    while p< nx:
        ch= int(32.0*(xpos[p]))
        ch = min(31, ch)
        xnum.append(ch)        
        p+=1
    n=0
    u32=''
    while n< 32:
        if n in xnum:
            u32= u32+'M'
            # print n
        else:
            u32= u32+ '_'
        n+=1    
    l32= '________________________________'
    s32= '                                '

    bjlk=   {   'cf':[ '=|' + u32 + '  ',
                       '=|' + l32 + '| ',
                       '=|' + s32 + '  ' ],

                'hh':[ '  ' + u32 + '  ',
                       ' |' + l32 + '| ',
                       '/\\'+ s32 +'/\\' ],

                'ch':[ '=|' + u32 + '  ',
                       '=|' + l32 + '| ',
                       '=|' + s32 + '/\\' ],

                'cc':[ '=|' + u32 + '|=' ,
                       '=|' + l32 + '|=' ,
                       '=|' + s32 + '|='  ]   }

    return [ ind+ bjlk[end][0], ind+ bjlk[end][1], ind+ bjlk[end][2] ]

# -------------------------------------------------------------------------------
class Rectangle:
    def __init__(self, y, height, width, nbr=1):
        self.y = y
        self.h = height
        self.w = width
        self.nbr = nbr

    def elmstr(self):           # bevarer height negativ
        return 'yo=%6.2f: % d Rectang:  h=%6.2f  w=%6.2f' % \
                ( self.y, self.nbr, self.h, self.w)

    def npos(self):
        return self.h/2.0 + self.y

    def area(self):             # nbr*area klarer resten. -> E.A og rho.A
        return abs(self.h*self.w) * self.nbr

    def imom0(self):            # ref yPos, ej elem-kant !
        return self.area()*( self.h**2/12.0 + self.npos()**2)

class Triangle:
    def __init__(self, y, height, width, nbr=1):
        self.y = y
        self.h = height
        self.w = width
        self.nbr = nbr

    def elmstr(self):           # bevarer height negativ
        return 'yo=%6.2f: % d Triangl:  h=%6.2f  w=%6.2f' % \
                ( self.y, self.nbr, self.h, self.w)

    def npos(self):
        return self.h/3.0 + self.y

    def area(self):             # nbr*area klarer resten. -> E.A og rho.A
        return abs(self.h*self.w)/2.0 * self.nbr

    def imom0(self):            # ref yPos, ej elem-kant !
        return self.area()*( self.h**2/18.0 + self.npos()**2)

class CirTube:
    def __init__(self, y, height, width, nbr=1):
        self.y = y
        self.h= height
        self.w= width
        self.nbr = nbr

    def elmstr(self):
        return 'yo=%6.2f: % d CirTube:  D=%6.2f  d=%6.2f' % \
                ( self.y, self.nbr, self.h, self.w )

    def npos(self):
        return self.h/2.0 + self.y     # fortegn paa height

    def area(self):
        return 0.7854*(self.h**2 - self.w**2) * self.nbr    #  pi/4 (D²-d²)

    def imom0(self):    #   D⁴-d⁴ = (D²+d²)(D²-d²)
        return self.area()*( (self.h**2+self.w**2)/16.0 + self.npos()**2 )

class Profile:  # ------------------------------------------------------------
    def __init__(self):
        self.lst = []

    def add(self, elem):    # add stigende yo rekkefolge
        if len(self.lst):
            if elem.y >= self.lst[-1].y:
                self.lst.append( elem)
            else:
                indx=0
                for el in self.lst:
                    if elem.y < el.y:
                        self.lst.insert( indx, elem)
                        return
                    else:
                        indx +=1
        else:
            self.lst.append(elem)

    def delete(self, elemno):
        nelems= len(self.lst)
        if (0<=elemno<nelems):
            del self.lst[elemno]

    def lstElem(self):
        lelm=[]
        for elem in self.lst:
            lelm.append( elem.elmstr() )
        return lelm

    def area(self):
        a = 0.0
        for el in self.lst:
            a += el.area()
        return a

    def imom0(self):
        im0 = 0.0
        for el in self.lst:
            im0 += el.imom0()
        return im0

    def npos(self):
        areaproduct = 0.0
        for el in self.lst:
            areaproduct += el.area()*el.npos()
        if self.area() != 0:
            return areaproduct / self.area()
        else:
            return 0.0

    def imomN(self):
        imN = self.imom0()-self.area()*self.npos()**2
        return imN

# end Profile    ----------------------------------------------------------

# start values --------------------------------------------------------------
tabl = {  'steel'  : {'E': 2.1e11, 'd': 7.9e03 },
          'alumin' : {'E': 7.0e10, 'd': 2.7e03 },
          'titan'  : {'E':1.17e11, 'd':4.45e03 },
          'copper' : {'E': 1.0e11, 'd': 8.9e03 },
          'lead'   : {'E': 1.7e10, 'd':1.13e04 },
          'pcb'    : {'E': 3.0e10, 'd': 2.0e03 },
          'glass'  : {'E': 7.5e10, 'd': 3.5e03 },
          'wood'   : {'E': 1.3e10, 'd': 6.0e02 },
          'abs,pc' : {'E': 2.2e09, 'd': 1.2e03 },
          'pa6,pom': {'E': 3.0e09, 'd': 1.2e03 }  }

fix = {'cf':'Clamp-Free', 'hh':'Hinge-Hinge', 'ch':'Clamp-Hinge', 'cc':'Clamp-Clamp' }
bdim = 9   # beam simulated numerically by 'bdim' equidistant discrete masses
sTab4= '                '   # 16 spaces = 4 tabs
subject= ''
length=  0.53           # L = 53 cm
mater=  'steel'         # giver E og d(ensity)
profil= Profile()       # Cross section cm: ----------
profil.add( Rectangle( 0,   3, 0.3, 1))   # ypos, height, width, nbr
profil.add( Rectangle( 3, 0.3,   5, 1))
profil.add( Rectangle( 3.3, 3, 0.3, 1))
user_sect= 0            # =0: use profil elements, =1: direct input of I & A
Iuser= 8091.0           #
Auser= 91.04
ends=  'hh'             # hinge - hinge
xpring= 0.01            # x for k(x), display kun for > 0.01 !!!
Meven=  0.0             # even load. Mbeam + Meven = total distrib Mdist
pmm =   [[ 0.5, 1.0]]   # point mass matrix, start 1 kg i midten
pdim=   len(pmm)

cwdir=os.getcwd()
openflag=0
calcflag=1
saveflag=0

while True:     # ------------------------------- resten af script ---------------------------------
  
    if openflag:  # -----------------------------------------
        openflag=0
        fobj= open( fname, 'r')
        print " Opened file %s" % fname
        profil.lst=[]
        ypos=0
        pmm=[]
        user_sect=0
        for line in fobj:
            line= line.strip()      # fjerne indledende spaces
            lstrg= line.split( None, 1)    # 1.ord + resten( ='Subj.')            
            line= line.lower()
            lFlts= textool.floatex( line)  # list of floats found in line
            nFlts= len( lFlts)
            if line.startswith( 'sub') and len(lstrg)>1:     # Subj: teksten
                subject= lstrg[1]
            elif line.startswith( 'end'):       # end conditions C, F, H
                for key in fix:
                    if line.count( fix[key].lower() ):
                        ends= key
            elif line.startswith( 'mat'):
                for key in tabl:                # undersog hvert materialenavn i tabl
                    if line.count( key[:4]):    # hvis aktuelle line indeholder 3 forste navn bogst.
                        mater= key
            elif line.startswith( 'len') and nFlts:     # length of beam  
                length= lFlts[0]/100.0

            elif line.startswith('sec') and nFlts==2:   # user Imom og Area
                user_sect=1
                Iuser=lFlts[0]
                Auser=lFlts[1]
            elif line.startswith( '#') and nFlts >1:    # et sect element 
                width = lFlts[-1]       # hvis mindst to tal
                height= lFlts[-2]
                nbr=1
                if nFlts >2:            # mindst 3 tal
                    nbr   = lFlts[-3]
                    if nFlts >3:        # mindst 4 tal    
                        ypos  = lFlts[-4]
                if line.count('rec'):   # Rectangle
                    elem = Rectangle( ypos, height, width, nbr )
                    profil.add( elem)
                elif line.count('tri'): # Triangle
                    elem = Triangle( ypos, height, width, nbr )
                    profil.add( elem)
                elif line.count('cir') or line.count('tub'): # Circular tube
                    elem = CirTube( ypos, height, width, nbr )
                    profil.add( elem)
                ypos+=height
                
            elif line.startswith( 'even') and nFlts:    # even load      
                Meven = lFlts[0]
            elif line.startswith( 'x') and nFlts==2:    # point mass at x
                pmm.append([ lFlts[0], lFlts[1] ])
        fobj.close()
        if profil.lst==[]:
            calcflag=0
            print ' Error: No section/profile defined !'
        else:
            calcflag=1

        
    # -------------------------------------------------------

    if calcflag:  # -----------------------------------------
        calcflag=0      # forbered strings m tal som psdk og print

        if user_sect == 0:          # Tvarsnit sammensat af elementer 
            Imom = profil.imomN()
            Area = profil.area()
            sSecProp = ' -> I= %7.2f cm4,   A= %5.2f cm2,  n= %5.2f cm' %(Imom, Area, profil.npos())
        else:
            Imom = Iuser            # User indtaster I og A direkte 
            Area = Auser
            sSecProp = ' -> I= %7.2f cm4,   A= %5.2f cm2' %( Imom, Area )
            
        Mbeam = tabl[mater]['d'] * Area/1e04 * length   # beams own mass
        Mdist = Mbeam + Meven    # total distributed mass
        
        Mnum = 1.0*Mdist/bdim
        bmm=[]          # beam mass matrix
        p=0

        while p < bdim: # afst mell Mnum er 1/bdim, i pos ½, 1½, 2½ etc
            bmm.append( [ (p+0.5)/bdim, Mnum] )
            p+=1
        
        K = tabl[mater]['E'] * Imom/1e08 / length**3    # K = EI/L³
        spring= 6*K/alfa( ends, xpring, xpring)         # Fjederkonstant N/m i pkt xpring 
        
        Frq0 = np.sqrt( K*lofrq( ends, bmm+pmm)[0]) /6.2832    # lowest
        Frq1 = np.sqrt( K*lofrq( ends, bmm+pmm)[1]) /6.2832    # next lowest

        sEnds    = ' Ends lft-rgt:   %s' %( fix[ends])
        sMaterial= ' Material:       %s beam    E= %4.2e N/m2,  d= %4.2e kg/m3' %\
                    ( mater.capitalize(), tabl[mater]['E'], tabl[mater]['d'] )
        sLength  = ' Length, L:      %-5.1f cm' % (length* 100.0)
        sEven    = ' Even load:      %-6.3f kg    Mbeam = %6.3f kg' % (Meven, Mbeam)
        sFreq = '\n      Lowest nat. freq. of beam: %6.1f Hz    (next lowest: %5.0f Hz)' % (Frq0, Frq1)
        sSpring  = ' Spring const.:  k(x)= %5.2e N/m  at x*L, x= %4.2f' %( spring, xpring)        

        clear_screen()
        print '              Natural frequency of uniform beam w/wo point mass(es).' 
        print sTab4+sTab4+'Type H(elp) or Q(uit)'
        print ' ============================================================================='
        print ' Subj: '+ subject
        print ' -----------------------------------------------------------------------------'
        print sEnds
        print sMaterial
        print sLength
        print
        if user_sect == 0:
            print ' Section:        elements, cm:'
            n= len( profil.lstElem() ) -1
            while n>=0:
                print sTab4 + ( ' #% 2d: ' % n) + profil.lstElem()[n]
                n-=1
            print sTab4 + sSecProp
        else:
            print ' Section:        user values:    '+ sSecProp

        print
        print sEven
        print ' Point loads:    at x*L from left:'
        pdim = len( pmm)
        if pdim:
            n=0
            while n <pdim:
                print sTab4 + (' x= %4.2f : %6.3f kg' % (pmm[n][0], pmm[n][1]))
                n +=1
        else:
            print sTab4+ ' None'
        xpos=[]
        n=0
        while n< pdim:
            xpos.append(pmm[n][0])
            n +=1
        
        lbmstr= Beam( ends, xpos, sTab4+'    ' )
        print
        print lbmstr[0]
        print lbmstr[1]
        print lbmstr[2]
        print sFreq
        print '                                =========='
        if xpring > 0.01:
            print sSpring
        print ' -----------------------------------------------------------------------------'
        print
    # end calcflag ------------------------------------------   

    if saveflag:  # -----------------------------------------
        saveflag=0
        fobj= open( fname, 'w')
        fobj.write( ' =============================================================================\r\n' )
        fobj.write( ' Subj: '+ subject +'\r\n') 
        fobj.write( ' -----------------------------------------------------------------------------\r\n' )
        fobj.write( sEnds  + '\r\n')
        fobj.write( sMaterial + '\r\n')
        fobj.write( sLength +'\r\n')
        fobj.write( '\r\n Section:        elements, cm:\r\n' )
        n= len( profil.lstElem() ) -1
        while n>=0:
            fobj.write( sTab4+ (' #% 2d: ' % n) +profil.lstElem()[n] +'\r\n' )
            n-=1
        fobj.write( sTab4+ sSecProp + '\r\n')

        fobj.write( '\n\r' + sEven  + '\r\n')
        fobj.write( ' Point loads:    at x*L from left:\r\n')   
        pdim = len( pmm)
        if pdim:
            n=0
            while n <pdim:
                fobj.write( sTab4 + (' x= %4.2f : %6.3f kg' % (pmm[n][0], pmm[n][1])) +'\r\n')
                n +=1
        else:
            fobj.write( sTab4+ ' -none-\r\n')
        # her skulle 'tegnet' profil evt ind
        fobj.write( sFreq + '\r\n')
        fobj.write( '                                ==========\r\n')
        if xpring >0.01:
            fobj.write( sSpring + '\r\n')
        fobj.write( ' -----------------------------------------------------------------------------\r\n' )        
        fobj.close()
        print ' Beam Fo calculation saved to ' + fname + '\r\n'
                
    # end saveflag ---------------------     

    # Prompt og input ---------------------------------------------------------------

    print '\n Type leftmost word above, or SAve, OPen, Help, Quit: ',
    strng= raw_input()
    print
    if strng == '':
        calcflag =1             # tom strng, calcflag=1...
        continue
    # strng= strng.lower()
    strng= strng.strip()

    fstrg= textool.floatex(strng)
    nfstr= len(fstrg)
    lstrg= strng.split( None, 1)    # 1 ord + resten(subjekt!)
    nstrg= len(lstrg)
    strng= strng.lower()

    if strng.startswith('q') or strng.startswith('ex'):       # Quit = EXit
        break

    elif strng.startswith('sec') and nstrg> 1:
        if lstrg[1].startswith( 'use'):
            user_sect=1
            if nfstr> 0:
                Iuser= fstrg[ 0]
                if nfstr> 1:
                    Auser= fstrg[1]
            calcflag=1

        elif lstrg[1].startswith( 'ele'):
            user_sect=0
            calcflag=1     
    
    elif strng.startswith('sec'):      

        if user_sect ==1:
            print ' Section: user I and A'
            while True:
                print ' <enter> to accept I= %7.2fcm4, A= %5.2fcm2, or type new :' % ( Iuser, Auser)
                answ= raw_input(' ')
                if answ== '':
                    calcflag=1
                    break
                else:
                    lflts= textool.floatex( answ)
                    if len(lflts):
                        Iuser= lflts[0]
                        if len(lflts)>1:
                            Auser=lflts[1]

        elif user_sect==0:
            print ' Section: Input elements for calculation of Imom and Area :'          
            print " 'rec'  height  width   -adds one rectangle to top, or"
            print " yo  no  'RECtangle'  height  width    -all in cm"
            print " Similarly: 'TRIangle'  or  'TUBe' Diam diam."
            print " To delete all, type 'new', or <#> to delete one. (Voids !!)\n\r"
            while True:
                if len( profil.lst):
                    n= len( profil.lst) -1
                    while n>=0:
                        print '         #% 2d:' % n, profil.lstElem()[n]
                        n-=1
                print '\n\r   - <enter> to accept, or..',
                answ = raw_input(' ')
                if answ == '' and len(profil.lst):  # ingen retur UDEN PROFIL
                    calcflag=1
                    break
                lFlts = textool.floatex( answ )
                nFlts = len(lFlts)

                if answ.startswith('new'):      # sec new slet alle elem
                    profil.lst=[]
                    continue
                elif nFlts==1:                  # sec <nr>, slet elem nr
                    number = int( lFlts[0])     # Profile har selv bounds check
                    profil.delete( number )
                elif nFlts==2:
                    nbr = 1
                    height= lFlts[-2]
                    width = lFlts[-1]
                    if len(profil.lst):
                        ypos = profil.lst[-1].y + profil.lst[-1].h
                    else:
                        ypos=0
                elif nFlts==3:
                    nbr   = lFlts[-3]
                    height= lFlts[-2]
                    width = lFlts[-1]
                    if len(profil.lst):
                        ypos = profil.lst[-1].y + profil.lst[-1].h
                    else:
                        ypos=0
                elif nFlts==4:                   # yo angivet, saa ingen 'top'-autom... 
                    ypos  = lFlts[-4]
                    nbr   = lFlts[-3]
                    height= lFlts[-2]
                    width = lFlts[-1]

                if answ.count('rec'):    # Rectangle
                    elem = Rectangle( ypos, height, width, nbr )
                    profil.add( elem)
                elif answ.count('tri'):  # Triangle
                    elem = Triangle( ypos, height, width, nbr )  # her D og d
                    profil.add( elem)    
                elif answ.count('tub'):  # Circular tube
                    elem = CirTube( ypos, height, width, nbr )  # her D og d
                    profil.add( elem)

    elif strng.startswith('po') and nstrg>1:    # and # of words
        ptx= min( 0.99, fstrg[0])               # x<1, ogsaa 'cf' !
        ptx= max( 0.01, ptx )                   # x>0
        if nfstr==2:                            # of floats in strng
            pmm = InsPlace( pmm, [ ptx,fstrg[1]] )
        elif nfstr==1 and pdim:                 # kun delete hvis der er noget
            ndx=0
            for xml in pmm:
                if ptx <= xml[0]:
                    del pmm[ndx]
                    break
                ndx +=1
        calcflag=1
                
    elif strng.startswith('po'):    # Point mass load
        while True:
            pdim = len( pmm)
            if pdim:
                print ' Point mass loads'
                n=0
                while n <pdim:
                    print sTab4 + ('x= %4.2f : %6.3f kg' % (pmm[n][0], pmm[n][1]))
                    n +=1
            else:
                print ' -none-'
            print '  <enter> to accept,  <x> or "new" to delete,  or <x> <kg> to add : ',
            answ = raw_input( ' ')
            if answ == '':
                calcflag=1
                break
            answ= answ.lower()
            lFlts = textool.floatex( answ )     # kun space kan adskille param ..
            nFlts = len(lFlts)                  # no of numbers in list of numbers
            if nFlts == 2:                  # 2 tal point og mass
                ptx= min( 0.99, lFlts[0])
                ptx= max( 0.01, ptx )
                pmm = InsPlace( pmm, [ptx,lFlts[1]] )
            elif nFlts==1 and pdim:         # 1 tal: delete this x or next higher x
                ptx= lFlts[0]
                ndx=0
                for xml in pmm:
                    if xml[0] >=ptx:
                        del pmm[ndx]
                        break
                    ndx +=1
            elif answ.count( 'new'):
                pmm = []

    elif strng.startswith('sub') and nstrg >1:  
        subject= lstrg[1]
        calcflag=1
    elif strng.startswith('sub'):       # Subj: text string
        while True:
            print ' <enter> to accept'
            print ' '+ subject +' '
            print ' -or type new : ',
            answ= raw_input()
            if answ == '':
                calcflag=1
                break
            else:
                subject = answ

    elif strng.startswith( 'mat') and nstrg >1:
        for k in tabl:
            if k.count(lstrg[1]):
                mater=k
                break
        calcflag=1 
    elif strng.startswith('mat'):      
        for k in tabl:
            print '     %-8s  E= %4.2e N/m2   d= %4.2e kg/m3' % (k.capitalize(), tabl[k]['E'], tabl[k]['d'])
        while True:
            print '\n\r  <enter> to accept "%s" or type new : ' % mater,
            answ = raw_input()
            if answ == '':
                calcflag=1
                break
            for k in tabl:
                if k.count(answ):
                    mater= k
                    break

    elif strng.startswith('len') and nstrg>1:
        length= fstrg[0]/100.0
        calcflag=1
    elif strng.startswith('len'):        # length
        while True:
            print ' <enter> to accept length %5.2f cm or type new : ' % (length*100.0),
            answ= raw_input()
            if answ == '':
                calcflag=1 
                break
            else:
                length = textool.floatex(answ)[0]/100.0
                
    elif strng.startswith('spr') and nstrg>1:
        xpring= max( 0.01, fstrg[0])
        xpring= min( 0.99, xpring )
        calcflag=1
    elif strng.startswith('spr'):       # spring constant
        while True:
            print ' Spring k(x)= %5.2e N/m for x= %4.2f. ' % ( 6*K/alfa( ends, xpring, xpring), xpring),
            print ' Type new x (0.1< x <0.9, x=0 to hide) or <enter> : ',
            answ= raw_input()
            if answ == '':
                calcflag=1
                break
            else:
                xpring= textool.floatex( answ)[0]
                xpring= min(0.99, xpring)
                xpring= max(0.01, xpring)

    elif strng.startswith('eve') and nstrg>1:
        Meven= fstrg[0]
        calcflag=1
    elif strng.startswith('eve'):        # even mass
        while True:
            print ' <enter to accept even load %6.3f kg or type new : ' % Meven,
            answ= raw_input()
            if answ == '':
                calcflag=1
                break
            else:
                Meven = textool.floatex( answ)[0]

    elif strng.startswith('end') and nstrg>1:
        if lstrg[1] in fix:
            ends= lstrg[1]
            calcflag=1
    elif strng.startswith('end'):       # ends fixing
        for key in fix:
            print '     ' + key + ' : ' +  fix[key]
        while True:
            print '\n\r  <enter> to accept %s, or type new code : ' % ( ends),
            answ = raw_input()
            if answ == '':
                calcflag=1
                break
            answ= answ.lower()
            if answ in fix:
                ends= answ
            else:
                ends='hh'

    elif strng.startswith('bdim'):    # No of points to simulate beam+even mass
        while True:
            print ' No. of discrete masses simulating distributed (beam+even) mass (%d) : ' % bdim,
            answ = raw_input()
            if answ == '':
                calcflag=1
                break
            elif answ.isdigit():
                bdim = int( answ)

    elif strng.startswith('sa'):    # SAve list
        print ' Save to Curr.Work.Dir.: %s' % cwdir                
        while True:
            fname= raw_input( ' Save filename[.txt]: ')
            if fname =='':
                break
            elif not fname.count('.'):
                fname= fname+'.txt'
            if os.path.exists( fname):
                print ' %s exists, -overwrite ?' % fname,
                answ= raw_input()
                if answ in ['y','Y']:
                    saveflag=1
                    break
            else:
                saveflag=1    
                break

    elif strng.startswith('op'):    # OPen file  - .txt listes
        print ' Curr.Work.Dir.: %s' % cwdir
        filist= [f for f in os.listdir('.') if f.endswith('.txt')]
        i=0
        for fil in filist:              # selekt nummer i)
            print ' %3d) %s' % ( i, fil)
            i +=1
        filnum= raw_input( ' Open file number (or <ent>): ')
        if filnum =='':                 # enter -> ovrige filer tilfojes
            filist.extend( [f for f in os.listdir('.') if not f.endswith('.txt')])
            while i < len(filist):      # fil nr i er next..
                print ' %3d) %s' % ( i, filist[i])
                i +=1
            filnum= raw_input( ' Open file number (or <ent>): ')
        if filnum != '':                # enter igen exit'er open file
            fname= filist[ int(filnum)]
            openflag=1


    elif strng.startswith( 'h'):    # Help
        print ' Natural frequency of prismatic beams with or w/o point loads.\n\r \
Type any of the leftmost words above (or at least 3 chars) to change parameters.\n\r\n\r \
Beam cross section is composed of stack\'ed elements (rectangles/triangles/tubes).\n\r \
"Horizontal" positions are not used, since only "vertical" bending is considered.\n\r \
The vertical stacking is overruled by giving vertical position yo for an element. \n\r\n\r \
Type "sect user" to alternatively give Imom & Area directly. "sect elem" returns. \n\r\n\r \
Save/open to/from text files in current working directory. Text approx as screen.\n\r\n\r \
Open file example:\n\r \
If a line starts with "#" and contains "rec" "tri" or "tub", and some numbers, \n\r \
then the last no.s are read into yo, no, height and width, in reverse, if found. \n\r\n\r \
"spring" and "bdim" are secret options.\n\r'

















