#!/usr/bin/env python

def floatex( strn, pnt='.,'):   # ------ 2013-06-13  ----------------------------------
    '''
    Returns list of floats found in string argument. e/E-nn included.
    Goal: If a human can find the numbers in a string, this program should too,
    Except: floats are also extracted from names/units, like 2.0 from m^2 or g2/Hz
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
# end def floatex -----------------------------------------
 
if __name__ == '__main__':
    print "\nTest: list-of-floats= floatex('string-with-numbers').  <ent> quits"
    while True:
        mixtr= raw_input( 'Test-string: ') 
        if mixtr=='':
            break
        print 'Dec point: ',
        print floatex( mixtr, '.')
        print 'Dec comma: ',
        print floatex( mixtr, ',')
        print 'Dec both : ',
        print floatex( mixtr)
        
        
