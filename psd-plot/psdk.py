#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import numpy as np          # evt endre til import math (as np -til test) 
import matplotlib.pyplot as plt
import matplotlib as mpl    # endre size figure 1  mv
import sys
import os
import textool

# 2013-07-07: Herefter er maalet: kun test for 'bugs' !
# Nu psd-list-of-strings -til print baade skerm, fil og paa plot, 'monospace'
# Plot m begge enheder, sperret for mix, og advarsel hvis unit ej i aabnet fil
# py2exe ...
# Separate senere projekt(er): lin-log, RV-response. 

def findex( mtrix, val):  # ------------------------------------------------
    '''Find index: 2D matrix= list of lists. Return 1.index n hvor val<= mtrix[n][0]'''
    # mtrix[n]='line'='row'=indre list. val passer lige inden el. PAA n i stigende sekvens sorteret m line[0].
    indx=0
    for line in mtrix:
        if line[0] >= val:
            return indx
        indx +=1
    return -1       # der var ikke nogen, saa returner sidste index !
# end def findex  -----------------------------------------------------------

def insplace( mtrix, line):     # ------------------------------------------- 
    '''list 'line' inserted in list-of lists sorted by line[0], -or replace if ='''
    if len(mtrix):                  # hvis der er mindst 1 linie saa
        if line[0] > mtrix[-1][0]:          # hvis > sidste saa
            mtrix.append( line)             # append efter sidste i matrix
        else:                               # ellers er < sidste i matrix, og
            indx= findex(mtrix,line[0])     # finder ndx saa line[0] <= mtrix[ndx][0]
            if line[0]==mtrix[indx][0]:     # hvis desuden lig exist linie
                del mtrix[indx]             # saa skal gl linie slettes -'replace'
            mtrix.insert( indx, line)       # inden nye indsert'es
    else:                           # tom mtrix, saa
        mtrix.append( line)                 # blot append
    return mtrix
# end def insplace  ---------------------------------------------------------

def msqsegm( wfb, wfa, lfr):    # -------------------------------------------
    '''Integr w=wa(f/fa)^A, a->b, wfx= wx*fx, and "log frq ratio" lfr=ln(fb/fa)'''
    # returns mean square for segment
    # A=ln(wb/wa)/lfr, dB/oct=10*log10(2)*A=3.0103*A, lpr/lfr= A+1= B
    lpr = np.log(wfb/wfa )  # "log product ratio". Nat.log: ln() !
    if -0.5 < lpr < 0.5:
        return lfr*np.sqrt(wfb*wfa*( 1+lpr**2/12.0))
                        # MS^2= lfr^2* wb*wa* (1+ lpr^2/12+ lpr^4/360+ ..)
    else:
        return lfr*(wfb-wfa)/lpr    # = (wfb-wfa)/B
# end def msqsegm   ---------------------------------------------------------    

def rmstotal( mtix):   # ---------------------------------------------------
    # 2013-06-16. Alt regnes saa det passer m 'acc-enhed' [m/s2], dog displ m->mm her. 
    # Hvis det saa var [9.81m/s2] saa skal retur displ og veloc eftflg ganges med 9.81
    # Linier forudsat i freq-rekkefolge.
    # Til hvert breakpoint, Freq og ASD, adderes dB/oct-til-efterflg-breakpoint.
    # rms^2 (mean square) af acc, vel og displ akkumuleres. 
    amsq=0;  vmsq=0;  dmsq=0
    nbpts= len( mtix)
    if nbpts:                # Spring alt over hvis bm tom
        mtix[-1][2]= 0.0     # sidste, evt eneste, bpt linie: dB/oct=0 = "ingen slope"
        afa= mtix[0][1]*mtix[0][0]              #  asd *f
        vfa= mtix[0][1]/39.48/mtix[0][0]        # (m/s)^2/Hz*f: w/( 4*pi^2*f^2) *f
        dfa= mtix[0][1]*641.6/mtix[0][0]**3     # (mm)^2/Hz *f: w*1000^2/(16*pi^4*f^4) *f
        p=1
        while p < nbpts:
            afb= mtix[p][1]*mtix[p][0]
            vfb= mtix[p][1]/39.48/mtix[p][0]
            dfb= mtix[p][1]*641.6/mtix[p][0]**3                
            if (mtix[p][0] -mtix[p-1][0]) < 0.095:  # fb ca= fa, kun diff >= 0.1 Hz bidrager 
                mtix[p-1][2]= 0.0                   # ingen dB og ingen flg. mean-square's.
            else:
                lfr = np.log( mtix[p][0]/mtix[p-1][0])   # log freq ratio, ln(fb/fa)
                mtix[p-1][2]= 3.01*np.log( mtix[p][1]/mtix[p-1][1])/lfr # dB/oct kun listning
                amsq += msqsegm( afb, afa, lfr)     # mean square segment
                vmsq += msqsegm( vfb, vfa, lfr)
                dmsq += msqsegm( dfb, dfa, lfr)
            afa= afb;   vfa= vfb;   dfa= dfb
            p+= 1                                   # her opr sekvens a, v, d
    return [ np.sqrt(amsq), np.sqrt(vmsq), np.sqrt(dmsq)]
# end def rmstotal ----------------------------------------------------------

# -------------------------------------------------------------------------------------------------------
bm=[]      # break point matrix, en rekke linier, en linie per break point
openflag=0
calcflag=0
saveflag=0
plotflag=0
pltOn=0

asdstrn= ['m2/s3', 'g2/Hz']
accstrn= ['m/s2', 'g']
ymax= [100.0, 1.0]  
unit=1                              # index unit 1 for g enheder
lCols= ['blue','green','red','black','darkcyan','magenta']
num = -1
txt_ypos= 0.98

titel= 'Power Spectral Density'     # vises over plot, ej fil
bplist='PSD list/curve'             # gemmes og hentes fra fil

argcnt= len( sys.argv)
fname=''
if argcnt>1:           # Fil eller directory angivet paa cmd line
    cmdline = sys.argv[-1]          # sidste, saa evt default i shortcut ok!
    if os.path.isdir(cmdline):              # directory paa cmd line
        os.chdir( cmdline)
    elif os.path.isfile(cmdline):           # fil paa cmd line
        fname= os.path.basename(cmdline)
        openflag=1    
        cwdir= os.path.dirname(cmdline)     # filens pathname
        if cwdir != '':                     # er kun angivet hvis ikke CWD 
            os.chdir(cwdir)
cwdir= os.getcwd()
print '\n Type PSD breakpoints, or h[elp], or q[uit].  Any file open/save refer to'
print ' current folder/directory: %s' % cwdir
print
plt.ion()                   # setter interactive='True' i /etc/matplotlibrc
mpl.rcParams['figure.figsize']=[7.5,7.5]        # 10.0,7.5 fin til 3x4 dec
mpl.rcParams['xtick.major.size']=10             # default var 4 og 2
mpl.rcParams['xtick.minor.size']=5
mpl.rcParams['ytick.major.size']=10
mpl.rcParams['ytick.minor.size']=5
mpl.rcParams['font.family']='monospace'         # ellers i plt.txt: ,family='monospace')

while True:

    if openflag:
        openflag=0
        fobj= open( fname, 'r')
        print " Opened file %s" % fname
        bm=[]
        unit+= 2         # saa hvis ikke endret, saa ej unit info i fil, og -=2 tilbage
        for line in fobj:
            line= line.strip()                      # strip men ej lower..
            if len( line):
                if line.startswith('List: '):
                    bplist= line[6:]
                elif line.startswith('RMS:'):       # unit uendret hvis ingen rms line
                    if ('g' or 'G') in line[-5:]:   # G_rms worst case
                        unit= 1
                    elif 'm/s' in line[-6:]:        # m/s**2 worst case
                        unit= 0
                elif line[0].isdigit():                              
                    lFloats= textool.floatex( line) # default 2. arg: '.,' !
                    if len( lFloats) >1:            # kun linier m >2 tal. El. -in [2,3] ?? (g2/Hz)
                        bm.append( [ lFloats[0], lFloats[1], 0.0] ) # db/oct= 0.0= ignore
        fobj.close()
        # check af bm, -var filen en bp-liste med freq i stigende sekvens ?
        nbpts= len( bm)
        if nbpts > 1 and bm[0][0] >0:   # 1.frq >0 => alle er 
            calcflag=1                  # medmindre flg ..
            # plotflag=1
            p=1
            while p < nbpts:
                if bm[p][0]==bm[p-1][0]:    # 2 ens frekv 
                    bm[p][0] += 0.01        # saa + 0.01 Hz til nxt
                elif bm[p][0]< bm[p-1][0] or bm[p][1]==0:
                    calcflag=0              # volapyk sekvens eller psd=0
                    bm=[]
                    break
                p+=1
        else:                           # else 1 bpt eller frekv=0
            calcflag=0
            # plotflag=0
            bm=[]
        if calcflag==0:
            print ' No breakpoints loaded from in this ASCII text file !'
            print " 1 breakpoint per line starting with a number & with 2 no's > 0,"
            print ' -and all frequencies in increasing order: Edit the text file !'
        if unit > 1:        # ingen unit info i fil (ville saa vere 0 el 1)
            unit-= 2
            print " Unit not found in file, so '%s' may be wrong.  SCale 9.81..." % accstrn[unit]
            print " -or add a line starting with 'RMS:' and ending with 'g' or 'm/s2'"
            raw_input()             
    # end openflag ---------------------        
        
    if calcflag:
        calcflag=0  
        rms_avd= rmstotal( bm )     # Fkt tilfojer dB/oct og beregner rms accel. veloc. og displacement
        if unit==1:
            rmstring= 'RMS: %.2fmm, %.2fm/s, %.2fg' % ( 9.81*rms_avd[2], 9.81*rms_avd[1], rms_avd[0])
        else:
            rmstring= 'RMS: %.2fmm, %.2fm/s, %.1fm/s2' % ( rms_avd[2], rms_avd[1], rms_avd[0])
        psdHdr = '   Hz     %s   dB/oct' % asdstrn[unit]
        decimals= 4+ 2*unit
        lPsdStr= []
        for bl in bm:
            PsdStr= ' %6.1f  %8.*f' % ( bl[0], decimals, bl[1] )
            if bl[2]:                       # dB/oct= 0 medtages ikke, 'ingen' slope
                PsdStr+= '% 6.1f' % bl[2]  # %<spc> vigtig, '+' -> ' ' align m '-' 
            lPsdStr.append( PsdStr)
        
        print '------------------------------------------'
        print ' Title: '+titel
        print '  List: '+bplist
        print '   '+rmstring
        print
        print '   '+psdHdr
        print '    ------  -------- ------'
        p=0
        for PsdStr in lPsdStr:             # for breakpoint line in matrix
            print '%2d' % p,               # %2 betyder samlet width 2
            print PsdStr
            p+=1
        print '------------------------------------------'    
    # end calcflag --------------------   

    if plotflag:
        plotflag=0
        if pltOn == 0:          # ny plot opened
            pltunit=unit        # gem til smlg flg curver
        elif unit != pltunit:
            print " No curve added, type 'unit' first !"
            continue
        num += 1
        if num== len( lCols):
            num=0
        pltOn=1
        txt_ypos-= 0.04
        ax= plt.subplot(111)    # ax=.. aht plt.text pos i ramme-coord's, med 'transform =.. osv'
        plt.loglog( [x[0] for x in bm], [y[1] for y in bm], lCols[num], linewidth=1.5 )
        plt.title( titel)
        plt.ylabel('PSD   '+asdstrn[unit])
        plt.xlabel('Frequency  Hz')
        plt.axis([1, 10000, 0.0001*ymax[unit], ymax[unit]])
        plt.grid(True, which= 'both')       # + evt linestyle= ':'
        plt.text( 0.10, txt_ypos, bplist, transform= ax.transAxes, color= lCols[num], fontsize=11)
        plt.text( 0.51, txt_ypos, rmstring, transform= ax.transAxes, color= lCols[num],fontsize=11)
        plt.draw()
    # end plotflag ---------------------

    if saveflag:
        saveflag=0
        fobj= open( fname, 'w')
        fobj.write( ' List: '+bplist+'\r\n')    # bpliste strng gemmes med
        fobj.write( '  '+rmstring+'\r\n\r\n')
        fobj.write( psdHdr+'\r\n')
        fobj.write( ' ------  -------- ------\r\n')
        for PsdStr in lPsdStr:
            fobj.write( PsdStr+'\r\n')
        fobj.close()
        print ' Breakpoint list saved to %s' % fname
    # end saveflag ---------------------     
    
    # Prompt og input.
    print ' Hz %s:' % asdstrn[unit],
    strng = raw_input()
    if strng == '':                 # tom streng, <ent>, beregn og print liste
        calcflag=1
        continue
    strng= strng.lower()            # tolower
    strng= strng.strip()            # evt indl og slut spc's fjernes
    lnbrs= textool.floatex( strng)  # list of numbers m sep '.,'
    nnbrs= len( lnbrs)              # antal tal fundet
 
    if nnbrs== 0:           # COMMAND, ingen tal i indtastning, og ikke tom jvf ovenfor
        if strng.startswith('q') or strng.startswith('ex'):        # Quit = EXit
            break
        elif strng.startswith('ti'):     # TItle ny, over plot figur
            print ' Title for plot: %s' % titel
            answ= raw_input( ' New title (or <ent>): ')
            if answ != '':
                titel= answ
                if pltOn:
                    plt.title( titel)
                    plt.draw()
        elif strng.startswith( 'psd'):  # PSD added to plot for last curve
            if pltOn:
                print ' Adding PSD list for last curve on plot'
                txt_ypos-= 0.04
                plt.text( 0.51, txt_ypos, 'PSD:', transform= ax.transAxes, color= lCols[num],fontsize=11)
                plt.text( 0.62, txt_ypos, psdHdr, transform= ax.transAxes, color= lCols[num],fontsize=10) 
                for PsdStr in lPsdStr:
                    txt_ypos-= 0.025
                    plt.text( 0.61, txt_ypos, PsdStr, transform= ax.transAxes, color= lCols[num],fontsize=10) 
                plt.draw()
            else:
                print ' PSD list NOT added to plot, -no plot !'
        elif strng.startswith('cl'):    # CLose plot, initier for ny plot
            print ' Closing plot window, ready for any new plot'
            num= -1
            txt_ypos= 0.98          
            plt.close()
            pltOn= 0
        elif strng.startswith('pl'):    # PLot eller add to plot
            if pltOn:
                print ' Adding curve to plot ...'
            else:
                print ' Plot window opened. Mouse-click here to re-focus !' 
            plotflag=1               
            
        elif strng.startswith('li'):    # LIste navn, ny, med i filer 
            print ' PSD list/curve name: %s' % bplist
            answ= raw_input( ' New name (or <ent>): ')
            if answ != '':
                bplist= answ
        elif strng.startswith('ne'):    # NEw list, delete all
            bm=[]
            bplist='PSD list/curve'
            calcflag=1
        elif strng.startswith('un'):    # UNit toggle m/s2 og g
            print ' Toggling units g <-> m/s2 etc.'
            fac2= 9.81*9.81                 # der er knap 100* saa mange af de smaa m2/s3
            if unit==1:                     # det er pt g'er
                for bl in bm:
                    bl[1]= bl[1]*fac2
                unit=0                      # 0= m2/s3
            else:                           # pt de smaa m2/s3
                for bl in bm:
                    bl[1]= bl[1]/fac2       # knap 100* mindre antal g'er                 
                unit= 1                     # 1= g
            calcflag=1
        elif strng.startswith('sc'):    # SCale 
            strn= raw_input( ' Scale rms-factor (expression allowed): ')
            strn= strn.replace( ',','.')    # evt komma ->punktum
            fact= eval( '1.0*'+strn)        # force float...
            print ' Scale all brk.pts for rms-factor= %6.3f ? ' % fact,
            answ= raw_input()
            if answ in ['y','Y']:           # f.eks. <ent> =abort, dvs. lommeregner
                fac2= fact*fact
                for bl in bm:
                    bl[1]=bl[1]*fac2
                calcflag=1
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
            print '\n Help:'
            print ' Type two nos. to add freq and PSD to breakpoint list. <enter> again to list.'
            print " The 2. no. can be dB/oct, if 'to'(-next) or 'from'(-prev.) is also written."  
            print ' One number alone (freq) deletes that breakpoint -or the first following.'
            print " If 'vertical slope' is given at f: enter the two PSDs at f and f + 0.01 Hz."
            print
            print " --- OR type a keyword:"
            print ' LIst-name, NEw list, UNit, SCale. SAve/OPen list: text-file in curr. folder:' 
            print ' -so start this prgm by drag & drop wanted folder (or file) onto prgm shortcut.'
            print 
            print ' PLot, TItle, PSD-list, CLose: Curves in separate GUI w.mouse scale & save options.'
            print ' After plots this text window may require re-focus with mouse or Alt-Tab'
            print

    elif nnbrs== 1:         # SLET, kun 1 tal = frekv fundet i streng
        if len( bm):                # hvis der er bp linie at slette..
            frek= lnbrs[0]              # indtastet frekvens
            if frek >= bm[-1][0]:       # hvis frek >= sidste, saa
                del bm[-1]              # slettes sidste linie
            else:                       # slettes frekv eller flg frekv
                ndx= findex( bm, frek)     
                del bm[ ndx]            # hvis f > frekv alle linier, saa bm[-1], =>slet sidste
        else:                       # else er der ingen hjemme, bm tom
            print ' No lines to delete !'

    elif nnbrs> 1:          # INSERT or REPLACE breakpoint. Mindst 2 tal, + evt codetext
        if ' to' in strng:              # frq og dB/oct to next
            codeflag=1
        elif ' from' in strng:          # frq og dB/oct from previous
            codeflag=2
        else:
            codeflag=0                  # frq og ASD
        if codeflag:
            frek= lnbrs[0]
            A =   lnbrs[1]/3.01
            lin= [frek, 0.0, 0.0]
            if len(bm):
                if codeflag== 1:                # dB to next line
                    if frek< bm[-1][0]:             # hvis der er en flg ELLER = linie
                        ndx= findex( bm, frek)      # saa find den
                        if bm[ndx][0]==frek:        # hvis = saa ref til eft.flg 
                            ndx+=1
                        lin[1]= bm[ndx][1]*( frek/bm[ndx][0])**A    # beregn og set asd
                        bm= insplace( bm, lin)      # insert foer, eller erstat exist frekv 
                    else:
                        print ' Add following ref line first !'
                elif codeflag== 2:              # dB from previous
                    if frek> bm[0][0]:              # hvis der er en foregaaende bp linie
                        ndx= findex( bm, frek)      # findex giver dog FLG bp, eller -1
                        if ndx == -1:               # -1, frekv > sidste, saa ref til sidste bm[-1] 
                            ndx = 0                 # ndx-1 peger saa ogsaa paa foregaaende bp
                        lin[1]= bm[ndx-1][1]*(frek/bm[ndx-1][0])**A # men brug forrige til regn
                        bm= insplace( bm, lin)
                    else:
                        print ' Add previous ref line first !' 
                else:
                    print ' Type "to" or "from" !'
            else:
                print ' Add ref line first !'

        else:                   # INSERT or REPLACE: FRQ og ASD, (codeflag=0, ej 'to' eller 'from')
            lin= [ lnbrs[0], lnbrs[1], 0.0]         # = frek, psd, adb
            bm= insplace( bm, lin)                  # insert or replace based on freq lin[0] 

