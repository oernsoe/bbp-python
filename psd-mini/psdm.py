#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import sys
import os
import subprocess

''' 
    PSD mini udgave. Fjernet alt med plot og numpy, og egne fkt fra NoMath, ikke py-math
    Separate senere projekt(er): lin-log, RV-response. 
    Dette er gendan af fejl-slettet udg. m opdateret 'insplace' fkt. 
    Ny frekv indenfor +/-0.01 endrer ikke denne men kun dens PSD.
    'Lodret linie' med +0.05 Hz.  Kun >=0.1 Hz-segmenter medregnes i rms.  
'''

if sys.platform.startswith( 'win'):
    def clear_screen():
        subprocess.call([ "cmd.exe", "/C", "cls" ])
else:
    def clear_screen():
        subprocess.call([ "clear" ])


def floatex( strn, pnt='.,'):   # ------ 2013-06-13  ----------------------------------
    '''
    Returner list af floats svarende til tal fundet i streng. Ogsaa e/E-nn.
    Hvis et menneske kan finde tallene i en streng, saa skulle denne fkt ogsaa kunne...
    Dog: floats bliver ogsaa 'udtrukket' fra navne/enheder, som f.eks. 2.0 fra m^2 eller g2/Hz
    '''
    NONDIG, DIGIT, INIPT, PTDIG, ELTR, E1DIG, E2DIG  = range( 7)
    state= NONDIG
    flst=[]
    nstr=''
    strng= strn+'a'             # sluttilst.garanti: NONDIG =>slut-tal gemmes..
    oldc=''                     # forrige c = '-' og ellers tom
    for c in strng:
        bNum = c.isdigit()      # bool-Nummer
        if state== NONDIG:      # ej ciffer og ej ptm igang. Tal starter kun her !
            if bNum:            # ciffer nu fundet
                nstr = oldc+ c  # og dette 1. opsamles incl evt '-'
                state= DIGIT    # og der skiftes til nr-tilstand
            elif c in pnt:      # nr kan dog beg m ptm/kma uden 0 foran
                tmpstr= oldc    # evt '-' skal smides ud hvis falsk alarm
                state= INIPT    # m mindre eftflg ciffer ogsaa mangler..

        elif state== DIGIT:     # int-inden/uden-ptm er igang
            if bNum:            # hvis ciffer
                nstr+= c        # saa opsaml og fortset tilstand
            elif c in pnt:      # 1.ptm/cma  efter dig(s) fundet
                nstr+= '.'      # og pktm opsamles
                state= PTDIG    # men skift eftflg tilst, nu ikke flere ptm...
            elif c in ['e','E']:
                state= ELTR
            else:               # alle mulige w.space, excl: pktm, komma og e/E 
                flst.append( float(nstr)) # stopper og gemmer igangv tal
                state= NONDIG   # og saa forfra
                
        elif state== INIPT:     # init ptm uden 0 krever eftflg. digit(s)
            if bNum:
                nstr= tmpstr+'0.'+c    # nstr tom ved start tal, saa..
                state= PTDIG    # og saa videre, uden flere ptm
            else:
                state= NONDIG   # og ptm ej opsamlet og ej evt '-'
                 
        elif state== PTDIG:     # nr-efter-pktm igang, ikke flere ptm
            if bNum:            # hvis digit saa 
                nstr+= c        # forts opsaml blot
            elif c in ['e','E']:
                state= ELTR
            else:               # mens bogst, pktm og andet w.space
                flst.append( float(nstr)) # stopper og gemmer igangv tal
                state= NONDIG   # og saa forfra
                
        elif state== ELTR:      # e/E modtaget, +/- eller digit krevet
            if c in ['+','-']:
                tmpstr = 'e'+c  # stadig muligt at det var falsk alarm
                state= E1DIG
            elif bNum:          # 1.ciffer ok, pos.eksponent uden + tegn
                nstr = nstr+'e'+c
                state = E2DIG
            else:               # ingen +/- eller ciffer, e/E var NONDIG 
                flst.append( float(nstr)) # stop/gem opr tal uden e/E
                state= NONDIG   # e/E falsk alarm
                 
        elif state== E1DIG:     # et 1.ciffer kreves efter fortegn
            if bNum:            # saa ikke falsk alarm, tmpstr bruges straks
                nstr= nstr+ tmpstr+ c
                state= E2DIG
            else:               # falsk alarm, e/E+/- var blot non-digit
                flst.append( float(nstr))
                state = NONDIG
                
        elif state== E2DIG:     # et 2.ciffer tilladt, (vi HAR et 1.ciffer)
            if bNum:
                nstr += c
            flst.append( float(nstr)) # uansett om 1 el 2 ciffre
            state = NONDIG
        
        if c=='-':              # obs: ny 2. 'if' uanset state, alle char 
            oldc= '-'
        else:
            oldc= ''

    return flst


def _LN( x):  # -----------------------------------------------------------
    '''
    ln(x), grundtal 'e', med opt rekkeudv der konv med x i omegn af 1.
    Optimeret Taylor kan udledes fra alm Taylor ved at danne:
    ln(1+x)-ln(1-x)= ln((1+x)/(1-x)) og saa subst m omv fkt paa hojre side.
    ln(x) = 2{ b + b³/3 + b⁵/5 + b⁷/7 + ... }   -hvor b= (x-1)/(x+1)    
    x~1 opnaas forst m gentaget ln(x*y)= ln(x)+ln(y)
    x mult/div m 2 hhv 1.1 og 1.01 indtil 0.995<=x0<=1.005.
    Hver gang sub/add pre-beregnede, indbyggede ln(2), ln(1.1), ln(1.01)..
    Hvorefter lnx= lnx0 + samlet add-led 
    '''
    
    if x<=0:
        print ' Error, "log(x<=0)" '
        return -1

    add= 0      # samlede additions-led til lnx0

    ln20 = 0.69314718055995   # ln(2.0)
    ln11 = 0.09531017980432   # ln(1.1)
    ln01 = 0.00995033085317   # ln(1.01)

    while x<0.7:
        x=x*2.0
        add= add-ln20
    while x>1.4:
        x=x/2.0
        add= add+ln20
    while x<0.95:
        x=x*1.1
        add= add-ln11
    while x>1.05:
        x=x/1.1
        add= add+ln11
    while x<0.995:
        x=x*1.01
        add= add-ln01
    while x>1.005:
        x=x/1.01
        add= add+ln01
    # 0.995 <= x <= 1.005

    b= (x-1)/(x+1)
    b2= b*b

    lnx= b
    R = b
    n = 3.0
    while n< 11.0:
        R= R*b2
        lnx= lnx+ R/n
        n+= 2.0
    lnx= lnx*2.0

    return lnx+ add


def _SQRT( x):     # -------------------------------------------------------
    '''
    Kvadratroden af x.
    Man starter med en rimelig formodning om resultatet, 1/2 antal ciffre,
    ellers skal typisk bruges ca 15 iterationer i stedet for ~5, for OK resultat.
    PS: 3.rod-algor: y= (2y + x/y^2 )/3. Men brug pow(x, 1/3) i alm Py, -uden math !!
    '''
    if x< 1e-14:
        return 0.0
    y=x
    if x<1.0:
        y= 1.0/y

    n= 1
    I= int( y)
    while I> 0:
        I = I>>1
        n+= 1
    # n er nu antal bin ciffre
    n= n>>1
    # nu halvdelen
    I= int(y)   # I genetabl.
    I= I>>n     # nu halve antal bin ciffre
    y= float(I)
    
    if y<1e-14:
        y= 1e-14
        
    if x< 1.0:
        y= 1.0/y

    n=1
    y1= (y+ x/y) / 2.0
    while ((y1-y) > 1e-20) or ((y-y1) > 1e-14):
        y= y1
        y1= (y+ x/y) / 2.0      # den egtl algoritme for sqrt !
        n+= 1
    return y1

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


def insplace( mtx, row):     # ------------------------------------------- 
    ''' List 'row' indsettes i mtx, list-af-rows, sorteret ved deres 1.element mtx[r][0] 
        Hvis row[0] er indenfor +/-0.01, endres 1.elem ikke, men resten erstattes m row[1:]
    '''
    pos= row[0]
    ndx= 0
    if (len(mtx)==0 ) or (pos > mtx[-1][0]+0.01 ):
        mtx.append( row)                # pos i row > eksisterende ..
    else:
        while pos > mtx[ndx][0]+0.01:   # slutter med pos <= 'trappetrinet'
            ndx +=1                     # hvor ndx der peger paa dette trin. 
        if pos > mtx[ndx][0] -0.01:     # Men hvis kun 0.01 mindre, saa vil vi
            row[0]= mtx[ndx][0]         # faktisk bevare gl pos i nye row
            del mtx[ndx]                # og saa erstat lig slet inden...
        mtx.insert( ndx, row)           # indset nye row her.
    return mtx
# end def insplace  ---------------------------------------------------------


def msqsegm( wfb, wfa, lfr):    # -------------------------------------------
    '''Integr w=wa(f/fa)^A, a->b, wfx= wx*fx, and "log frq ratio" lfr=ln(fb/fa)'''
    # returns mean square for segment
    # A=ln(wb/wa)/lfr, dB/oct=10*log10(2)*A=3.0103*A, lpr/lfr= A+1= B
    lpr = _LN(wfb/wfa )  # "log product ratio". Nat.log: ln() !
    if -0.5 < lpr < 0.5:
        return lfr*_SQRT(wfb*wfa*( 1+lpr**2/12.0))
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
                lfr = _LN( mtix[p][0]/mtix[p-1][0])   # log freq ratio, ln(fb/fa)
                mtix[p-1][2]= 3.01*_LN( mtix[p][1]/mtix[p-1][1])/lfr # dB/oct kun listning
                amsq += msqsegm( afb, afa, lfr)     # mean square segment
                vmsq += msqsegm( vfb, vfa, lfr)
                dmsq += msqsegm( dfb, dfa, lfr)
            afa= afb;   vfa= vfb;   dfa= dfb
            p+= 1                                   # her opr sekvens a, v, d
    return [ _SQRT(amsq), _SQRT(vmsq), _SQRT(dmsq)]
# end def rmstotal ----------------------------------------------------------

# -------------------------------------------------------------------------------------------------------
bm=[]      # break point matrix, en rekke linier, en linie per break point
openflag=0
calcflag=0
saveflag=0

asdstrn= ['m2/s3', 'g2/Hz']
accstrn= ['m/s2', 'g']
unit=1                              # index unit 1 for g enheder

titel= 'Power Spectral Density'     # vises over plot/list, ej fil
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
                    lFloats= floatex( line) # default 2. arg: '.,' !
                    if len( lFloats) >1:            # kun linier m >2 tal. El. -in [2,3] ?? (g2/Hz)
                        bm.append( [ lFloats[0], lFloats[1], 0.0] ) # db/oct= 0.0= ignore
        fobj.close()
        # check af bm, -var filen en bp-liste med freq i stigende sekvens ?
        nbpts= len( bm)
        if nbpts > 1 and bm[0][0] >0:   # 1.frq >0 => alle er 
            calcflag=1                  # medmindre flg ..
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
        clear_screen()
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
    lnbrs= floatex( strng)          # list of numbers m sep '.,'
    nnbrs= len( lnbrs)              # antal tal fundet
 
    if nnbrs== 0:           # COMMAND, ingen tal i indtastning, og ikke tom jvf ovenfor
        if strng.startswith('q') or strng.startswith('ex'):        # Quit = EXit
            break

        elif strng.startswith('ti'):     # TItle ny, over plot/list
            print ' Title for the lists: %s' % titel
            answ= raw_input( ' New title (or <ent>): ')
            if answ != '':
                titel= answ
          
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
        elif strng.startswith('sc'):    # SCale problemer i Win ?
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
            print ' Type two nos to add/repl freq and PSD to breakpoint list. <ent> again to list.'
            print " The 2. no. can be dB/oct, - if 'to'(-next) or 'from'(-prev.) is also written."  
            print ' One number alone (freq) deletes that breakpoint -or the first following.'
            print " If 'vertical slope' is given at f: enter the two PSDs at f and f + 0.05 Hz."
            print
            print " --- OR type a keyword:"
            print ' LIst-name, NEw list, UNit, SCale. SAve/OPen list: text-file in curr. folder:' 
            print ' -so start this prgm by drag & drop wanted folder (or file) onto prgm shortcut.'
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

