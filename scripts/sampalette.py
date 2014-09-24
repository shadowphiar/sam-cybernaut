#!/usr/bin/env python


from PIL import Image
import getopt
import sys
import random
from os import path
import subprocess
import gzip
import re


def bit(b, n):
    return  (int(n) >> b) & 0x1


def rgb2sam((r_,g_,b_)):
    r = int(r_ / 36)
    g = int(g_ / 36)
    b = int(b_ / 36)

    p = bit(1,b) | bit(1,r)<<1 | bit(1,g)<<2 | bit(0,b) <<3 | bit(2,b)<<4 | bit(2,r)<<5 | bit(2,g)<<6

    return p
    
def sam2rgb(p):
    r = bit(3,p)*36 + bit(1,p)*73 + bit(5,p)*146
    g = bit(3,p)*36 + bit(2,p)*73 + bit(6,p)*146
    b = bit(3,p)*36 + bit(0,p)*73 + bit(4,p)*146
    
    print p, (r,g,b)
    
    return (r,g,b)
    
    
BLANKCOLOUR = 16
def sprite(y,x):
    x -= 1
    if (x<0) or (x>=width) or (y<0) or (y>=height):
      return BLANKCOLOUR
    if (newimage[x + (y*width)] == BLANKRGB) :
        return BLANKCOLOUR
    n = y*(width + (width%2)) + x
    p = samscreendata[n/2]
    if n%2:
        return p & 15
    else:
        return (p/16) & 15

def navigate(sprite,x,y,reverse):
    global dy, dx
    finished = 0

    testx = x
    testy = y

    navigateloop = 1
    
    
    if (height < width) and not VERTICALCOMPARE:
        
        while navigateloop:
            testy += dy
            if (testy < 0) or (testy > height-1):
                dy = -dy
                testy += dy
                testx += dx
                
                if testx > width+offset:
                    dx = -dx
                    testx += dx
                    
                    if not reverse:
                        testy += 1
                        if testy >= height:
                            testy -= 2
                    else:
                        testy -= 1
                        if testy < 0:
                            testy += 2
                elif testx < 0:
                    finished = 1
            if (sprite(testy,testx) != BLANKCOLOUR) or (sprite(testy,testx+1) != BLANKCOLOUR) or finished:    
                navigateloop = 0    

    else:
    
    
        while navigateloop:
        
            testx += dx
            if (testx > width+offset) or (testx < offset):
                dx = -dx

                testx += dx
                testy += dy
                
                if (testy > height-(not reverse)) and (dy>0):
                    dy = -dy
                    testy += dy
                    
                    if (not reverse):
                        testy += 1
                        
                    else:
                        testy -= 1

                elif testy < 0:
                    finished = 1
            if (sprite(testy,testx) != BLANKCOLOUR) or (sprite(testy,testx+1) != BLANKCOLOUR) or finished:    
                navigateloop = 0    

    return testx, testy, finished    




option_args, file_args = getopt.getopt(sys.argv[1:], 'lr:p:sb:do:x:y:macv:1XYRGqd')

MAXPALETTE = 16
# reduce this if some colours are reserved for other use (may be useful to detect black and use default 0)
NOLINEINTS = 0

MAKESPRITE = False
SPRITEMEMORY = True

MEMORYPAGE = True

BLANKPALETTE = 0

DITHER = False

palette = []

ODIR = None

MATRIX = [1,1]
ALIGNED = False
NOBACKGROUND = False
VERTICALCOMPARE = False

REPEAT = False
FINALOFFSET = []

BACKGROUNDCLIPPING = False

DIAGNOSTICS = True
DRAWLOOPID = False



for option,value in option_args:
    if option in ['-r']: # restrict
        MAXPALETTE=int(value)
        assert MAXPALETTE <= 16

        
    if option in ['-l','-s']: # limit
        NOLINEINTS = 1

    if option in ['-p']: # palette
        for v in value.split(','):
            palette.append(sam2rgb(int(v)))

    if option in ['-s']: # sprite
        MAKESPRITE = True

    if option in ['-m']: # by default, marshall calls through hmem
        SPRITEMEMORY = False

    if option in ['-1']: # allow the sprites in this file to choose appropriate pages for themselves
        MEMORYPAGE = False

    if option in ['-b']: # blank
        BLANKPALETTE = int(value)

    if option in ['-d']:
        DITHER = True

    if option in ['-o']:
        ODIR = value
 
    if option in ['-x']:
        MATRIX[0] = int(value)
    if option in ['-y']:
        MATRIX[1] = int(value)

    if option in ['-a']: # aligned
        ALIGNED = True # when making sprites, only bother with byte-aligned version, no extra right-pixel code

    if option in ['-c']:
        NOBACKGROUND = True
        
    if option in ['-v']:
        VERTICALCOMPARE = int(value)
 
    if option in ['-X']:
        FINALOFFSET.append('x')

    if option in ['-Y']:
        FINALOFFSET.append('y')

    if option in ['-R']:
        REPEAT = True

    if option in ['-G']:
        BACKGROUNDCLIPPING = True

    if option in ['-q']:
        DIAGNOSTICS = False
        
    if option in ['-d']:
        DRAWLOOPID = True # calculate a single-word identifier for each sprite, autoselecting L/R based on carry flag
    
BLANKRGB = sam2rgb(BLANKPALETTE)    

if (len(palette)==0): 
    palette.append((0,0,0))
    
    
RESERVEPALETTE = len(palette)    

if MAKESPRITE:
    MAXPALETTE = RESERVEPALETTE
elif BLANKPALETTE != 0 and MAXPALETTE == 16:
    MAXPALETTE = 15


if MAXPALETTE != 16:
    print "Restricting palette to",MAXPALETTE,"colours",
    if not NOLINEINTS:
        print "per line"
    else:
        print ""
else:
    if NOLINEINTS:
        print "No line interrupt changes"
    


for inputfilename in file_args:
    sourcecode=[]
       
    source_im = Image.open(inputfilename)
    width, height = source_im.size
    matrix_images = []
    
    drawn_masks = {}
    
    for j in range(MATRIX[1]):
        for i in range(MATRIX[0]):
            prefix = ''
            if MATRIX[0] > 1:
                prefix += "_"+str(i)
            if MATRIX[1] > 1:
                prefix += "_"+str(j)
        
            matrix_images.append(( prefix, source_im.crop( (i * width/MATRIX[0], j * height/MATRIX[1], (i+1) * width/MATRIX[0], (j+1) * height/MATRIX[1]) ) ))
    
    catalogue = {}
    
    for prefix, im in matrix_images:
    
        
        width, height = im.size
    
    
        # now inputfile is loaded, hack the path so tmp files are saved where specified
        inputfile = inputfilename + prefix
        if ODIR:
            inputfile = path.join(ODIR, path.basename(inputfile))
    
        
        pixels = im.convert("RGB").getdata()
        
        newimage = []
        random.seed(0)
        
        for y in range(height):
            for x in range(width):
                pixel = pixels[x + (y*width)]
                
                # find the eight nearest colours (1bit leeway on r,g,b,br)
                # find error for each colour, and pick randomly based on 1/error
                
                if not DITHER and catalogue.has_key((pixel[0],pixel[1],pixel[2])):
                    p = catalogue[(pixel[0],pixel[1],pixel[2])]
                else:
            
                
                    r0 = int((pixel[0] / 73.0))
                    if r0>2: r0=2
                    g0 = int((pixel[1] / 73.0))
                    if g0>2: g0=2
                    b0 = int((pixel[2] / 73.0))
                    if b0>2: b0=2
                
                
                    choices=[]
                    rangetotal = 0
                
                    try:
                        minError = None
                
                        for r in (r0, r0+1):
                            for g in (g0, g0+1):
                                for b in (b0, b0+1):
                                    for br in (0,1):
                                        p = ((73*r+36*br), (73*g+36*br), (73*b+36*br))
                                
                                        e = (p[0]-pixel[0]-10*br)**2 + (p[1]-pixel[1]-10*br)**2 + (p[2]-pixel[2]-10*br)**2
                                        choices.append((p, 1.0/e))
                                        rangetotal += 1.0/e
     
                                        if (minError == None) or e < minError:
                                            minError = e
                                            minErrorP = p
     
     
                        if DITHER:
     
     
                            choose = random.random()*rangetotal
                            while choose>0:
                                p,er = choices.pop()
                                choose -= er
    
                        else:
                            p = minErrorP
    
    
                    except ZeroDivisionError:
                        pass
                        # that's okay, means an exact match with p

                    catalogue[(pixel[0],pixel[1],pixel[2])] = p
    
                newimage.append(p)
            
        
        im.putdata(newimage)

        if DIAGNOSTICS:
            im.save(inputfile+".sampalette.png","")
                
        # now limit number of colours per line allowing 1 palette change per line
        
        # find what colours are used on each line
        
        coloursused = []
        for y in range(height):
        
            coloursinline = {}
        
            for x in range(width):
                pixel = newimage[x + (y*width)]
        
                if coloursinline.has_key(pixel):
                    coloursinline[pixel] += 1
                else:
                    coloursinline[pixel] = 1
        
            coloursused.append(coloursinline)
        
        
        
        # initial palette contains first MAXPALETTE used colours
        
        assert len(palette) <= 16
        
        if NOLINEINTS:
            coloursrequired = {}
            for y in range(height):
                 for colour,freq in coloursused[y].items():
                     if coloursrequired.has_key(colour):
                        coloursrequired[colour] += freq
                     else:
                        coloursrequired[colour] = freq
        
        else:
            for y in range(height):
                coloursrequired = {}
                for colour,freq in coloursused[y].items():
                    if not (colour in palette):
                        coloursrequired[colour] = freq
                if len (coloursrequired) <= (MAXPALETTE - len(palette)):
                    palette.extend(coloursrequired.keys())
                    assert len(palette) <= 16
                else:
                    break;
                    # best colours in coloursrequired will be added to palette
                
        # calculate severity of NOT including this colour in the palette (compared to choosing closet of other colours already in)
        severeties = []
        for required,frequency in coloursrequired.items():
            
            minerror = -1
    
            # what is the error per pixel if we use each available alternative colour? we'll use the least bad
            for potential in palette:
                e = (potential[0]-required[0])**2 + (potential[1]-required[1])**2 + (potential[2]-required[2])**2
                if (minerror > e) or (minerror < 0):
                    minerror = e
                    candidate = potential
    
            severeties.append((minerror * (frequency**2), required))
    
        severeties.sort()

        assert len(palette) <= 16
        
        while (((len(palette) < MAXPALETTE)) and (len(severeties)>0)):
            severity,colour = severeties.pop()
            if (BLANKPALETTE == 0) or (rgb2sam(colour) != BLANKPALETTE):
                palette.append(colour)
    
        sortpalette = palette[RESERVEPALETTE:]
        sortpalette.sort()
        palette = palette[:RESERVEPALETTE]
        palette.extend(sortpalette)
    
        assert len(palette) <= 16
                     
        sampalettedata = []
        for index in range(16):
            if len(palette) > index:
                sampalettedata.append(rgb2sam(palette[index]))
            else:
                sampalettedata.append(0)
        
        paletteimage = []
        samscreendata = []
        
        for y in range(height):
        # calculate what palette line change may be useful for the next line
            if y!=0 and not NOLINEINTS:
        
                coloursrequired = {}
                for colour in palette:
                    coloursrequired[colour] = 0
                
                for lookahead in range(y,min(height,y+2)):
                    for colour,freq in coloursused[lookahead].items():
                        if coloursrequired.has_key(colour):
                            coloursrequired[colour] += freq
                        else:
                            coloursrequired[colour] = freq
        
        
                severeties = []
        
                for required,frequency in coloursrequired.items():
                    
                    minerror = -1
        
                    # what is the error per pixel if we swap this colour in or out of the palette?
                    for potential in coloursrequired:
                        e = (potential[0]-required[0])**2 + (potential[1]-required[1])**2 + (potential[2]-required[2])**2
                        if ((minerror > e) or (minerror < 0)) and (e != 0):
                            minerror = e
        
                    severeties.append((minerror * (frequency**3), required))
        
                severeties.sort()
        
        
                # for colours in the palette, search for a likely candidate to drop
                # for colours outside the palette, search for the most important to add
                # if these are worth swapping, swap them.
        
                for dropcandidate in severeties:
                    if (dropcandidate[1] in palette) and (palette.index(dropcandidate[1])  > RESERVEPALETTE):
                        break;
                
                severeties.reverse()
                for swapcandidate in severeties:
                    if not (swapcandidate[1] in palette):
                        break;
        
                if swapcandidate[0] > (1.1*dropcandidate[0]):
                    newindex = palette.index(dropcandidate[1])
                
                    palette[newindex] = swapcandidate[1]
                    assert len(palette) <= 16
                
                    sampalettedata.append(y)
                    sampalettedata.append(newindex)
                    sampalettedata.append(rgb2sam(swapcandidate[1]))
                   
            
        # write line with palette limitations
            assert len(palette) <= 16

            for x in range(width):
                pixel = newimage[x + (y*width)]
        
                minerror = -1
                
                for index in range(len(palette)):
                    potential = palette[index]
                    e = (potential[0]-pixel[0])**2 + (potential[1]-pixel[1])**2 + (potential[2]-pixel[2])**2
                    if (minerror > e) or (minerror < 0):
                        minerror = e
                        candidate = potential
                        candidateindex = index
                
                if BLANKPALETTE:
                    potential = sam2rgb(BLANKPALETTE)
                    e = (potential[0]-pixel[0])**2 + (potential[1]-pixel[1])**2 + (potential[2]-pixel[2])**2

                    if (minerror > e) or (minerror < 0):
                        minerror = e
                        candidate = potential
                        candidateindex = 15
                
                paletteimage.append(candidate)
                
                assert(candidateindex <= 15)
                
                if x%2:
                    samscreendata[-1] += candidateindex
                else:
                    samscreendata.append(candidateindex*16)
        
        
        sampalettedata.append(255)
        
        if NOLINEINTS:
            print "Sampalettedata: ",sampalettedata
        
        
        im.putdata(paletteimage)
        if DIAGNOSTICS:
            im.save(inputfile+".sampalette.limit"+str(MAXPALETTE)+".png","")
        
        
        if not MAKESPRITE:
            if not BLANKPALETTE:
                samscreendata.extend(sampalettedata)
                
            if BLANKPALETTE:
                # saving a screen with transparent areas (nibble 0xF is transparent)
                # we'll define a format which hopefully lets us save time decoding the result
                # (don't worry - much - about saving space, as gzip will achieve that for us)

                f = gzip.GzipFile(inputfile+".transscreen.mdat.gz", 'wb')

                blanks = 0
                for c in samscreendata:
                    if c == 255:
                        blanks += 1
                        if blanks == 256:
                            f.write(chr(255))
                            f.write(chr(0))
                            blanks = 0
                    else:
                        if blanks:
                            f.write(chr(255))
                            f.write(chr(blanks))
                            blanks = 0
                        f.write(chr(c))
                    
                f.write(chr(255))
                f.write(chr(255))
                f.write(chr(255))
                f.close()                
                
            else:
            
                f = gzip.GzipFile(inputfile+".samscreen.mdat.gz", 'wb')
                for c in samscreendata:
                    try:
                        f.write(chr(c))
                    except:
                        print "illegal screen byte",c
                f.close()
            
        
        else:
        
        
        # make executable sprite source code from samscreendata
            numpushes = 0
            numpops = 0
        
            
            
            sourcecode.append(inputfile.split('/')[-1]+".WIDTH: EQU "+str(width))
            sourcecode.append(inputfile.split('/')[-1]+".HEIGHT: EQU "+str(height))
            
            
            if ALIGNED:
                label = [None,""]
                offsets = [1]
            else:
                label = ["RIGHT","LEFT"]
                offsets = [1,0]


            if DRAWLOOPID:
                sourcecode.append( "    DS ALIGN 16" )
                sourcecode.append( inputfile.split('/')[-1]+"ID: EQU (2*$) + (@-PAGE)" )
                sourcecode.append( "    DS (@-PAGE)/2" )
                # specify address in range 0 - 0x7ff0 (bit 15 always 0) as AAAA AAAA AAAP PPPP

                if not ALIGNED:
                    sourcecode.append( "    JP c, DRAW"+inputfile.split('/')[-1]+"RIGHT" )
                        



            
            for offset in offsets:
              for setfinaloffset in (FINALOFFSET if FINALOFFSET else [None]):

                key = inputfile.split('/')[-1]+label[offset]
                if REPEAT:
                    key += "REPEAT"+setfinaloffset

                uid = "DRAW"+key






                if SPRITEMEMORY and MEMORYPAGE:
    
                    sourcecode.append( "    IF $>16384")
                    sourcecode.append( "        org $-16384")
                    sourcecode.append( "        @PAGE: EQU @-PAGE + 1")
                    sourcecode.append( "        ENDIF")    



                sourcecode.append( uid+":"  )  
                sourcecode.append( uid+"PAGE: EQU @-PAGE"  )  






                ts = 0


                if VERTICALCOMPARE:
                    sourcecode.append( "ld a,h" )
                    ts += 4
                    sourcecode.append( "cp " + str(128+VERTICALCOMPARE/2) )
                    ts += 8
                    sourcecode.append( "jp nc, HMEM_SWITCH_LMEM_DRAW_RETURN" )
                    ts += 12
            
                # assume this routine will be called within low memory with the screen in high memory
                # HL is the address to draw into
                    # assume all registers will be corrupt:
                
                    # use DE for storing screen bytes which get pushed
                    # use bc for anding at screen edges, or possibly storing data in time
                
                
                
                routine = []
                
                x= offset
                y=0
                dx = 2
                dy = 2
                
                storebackgroundreg = 0
                
                pixelsstored = []
                
                
                b=-1
                c=-1
                
                finished = 0
                while not finished:
        
        

        
                    if (sprite(y,x)!=BLANKCOLOUR) or (sprite(y,x+1)!=BLANKCOLOUR):
                    
                        if not NOBACKGROUND:
                        
                            if not storebackgroundreg:
                                routine.append("ld d,(hl)")
                                ts += 8
                                pixelsstored.append((x,y))
                                bgreg = 'd'
                            else:
                                routine.append("ld e,(hl)")
                                ts += 8
                                routine.append("push de")
                                ts += 12
                                numpushes += 1
                                pixelsstored.append((x,y))
                                bgreg = 'e'
                        
                            storebackgroundreg = (storebackgroundreg + 1) % 2
                    
                        if (sprite(y,x)!=BLANKCOLOUR) and (sprite(y,x+1)!=BLANKCOLOUR):
                            if BACKGROUNDCLIPPING:
                                routine.append("bit 7,"+bgreg)
                                routine.append("jr z,@+clip0X")
                                routine.append("bit 3,"+bgreg)
                                routine.append("jr nz,@+clip11")
                                routine.append("@clip10: ld a,"+bgreg)
                                routine.append("and 15")
                                routine.append("or b")
                                routine.append("ld (hl),a")
                                routine.append("jr @+clipend")
                                routine.append("@clip0x:bit 3,"+bgreg)
                                routine.append("jr z,@+clipend")
                                routine.append("@clip01: ld a,"+bgreg)
                                routine.append("and 240")
                                routine.append("or c")
                                routine.append("ld (hl),a")
                                routine.append("jr @+clipend")
                                routine.append("@clip11: ld a,b")
                                routine.append("or c")
                                routine.append("ld (hl),a")
                                routine.append("@clipend:")
                                ts += 80
                            else:
                                routine.append("ld (hl),"+str(sprite(y,x)*16 + sprite(y,x+1)))
                                ts += 12
                        elif (sprite(y,x)!=BLANKCOLOUR):
                            if BACKGROUNDCLIPPING:
                                routine.append("bit 7,"+bgreg)
                                routine.append("jr z,@+clipend")
                                routine.append("@clip10: ld a,"+bgreg)
                                routine.append("and 15")
                                routine.append("or b")
                                routine.append("ld (hl),a")
                                routine.append("@clipend:")
                                ts += 48
                            else:                        
                                if NOBACKGROUND:
                                    routine.append("ld a,(hl)")
                                else:
                                    routine.append("ld a,"+bgreg)
                                ts += 4
                                routine.append("and 15")
                                ts += 8
                                l = sprite(y,x)*16
                                if l > 0:
                                    routine.append("or "+str(l))
                                    ts += 8
                                routine.append("ld (hl),a")
                                ts += 8
                        else:
                            if BACKGROUNDCLIPPING:
                                routine.append("@clip0x:bit 3,"+bgreg)
                                routine.append("jr z,@+clipend")
                                routine.append("@clip01: ld a,"+bgreg)
                                routine.append("and 240")
                                routine.append("or c")
                                routine.append("ld (hl),a")
                                routine.append("@clipend:")

                            else:                        
                                if NOBACKGROUND:
                                    routine.append("ld a,(hl)")
                                else:
                                    routine.append("ld a,"+bgreg)
                                ts += 4
                                routine.append("and 240")
                                ts += 8
                                l = sprite(y,x+1)
                                if l>0:
                                    routine.append("or "+str(l))
                                    ts += 8
                                routine.append("ld (hl),a")
                                ts += 8
    
                    lastx, lasty = x,y
                    testx, testy, finished = navigate (sprite, x, y ,0)
        
                    if finished:
                        if VERTICALCOMPARE:
                            routine.append("or a")
                            routine.append(uid+"finishup:")
                        
                        
                        if not NOBACKGROUND:
                            if storebackgroundreg:
                                routine.append("push de")
                                ts += 12
                                numpushes += 1
    
                            routine.append("push hl")
                            ts += 12


                        if setfinaloffset:
                            if setfinaloffset=="x":
                                finalx = width + offset
                                finaly = 0
                                cmpreg = 'L'
                                cmpoffset = int(width/2)
                            else:
                                finalx = offset
                                finaly = height
                                cmpreg = 'H'
                                cmpoffset = int(height/2)

                            finaloffset = (finaly-lasty)*128 + int((finalx-lastx)/2)
                            routine.append("ld de,"+str(finaloffset))
                            routine.append("add hl,de")

                        if REPEAT:
                            routine.append("ld a,"+cmpreg)
                            routine.append("add "+str(cmpoffset-1))
                            routine.append("exx")
                            routine.append("cp c")
                            routine.append("exx")


                        if not NOBACKGROUND:
                            routine.append("ld de,"+"REMOVE"+key)
                            ts += 12
                            routine.append("push de")
                            ts += 12

                        if REPEAT:
                            routine.append("jp c, DRAW"+key)

                        if SPRITEMEMORY:
                            if not NOBACKGROUND:
                                routine.append("ld a, REMOVE"+key+"PAGE" +" | 32")
                                ts += 8
                                routine.append("push af")
                                ts += 12
    
                                routine.append("ld de, HMEM_SWITCH_LMEM_REMOVE")
                                ts += 12
                                routine.append("push de")
                                ts += 12

                       
                            routine.append( "jp HMEM_SWITCH_LMEM_DRAW_RETURN")
                            routine.append( "; routine takes"+str(ts)+"tstates")
                        else:

                            routine.append( "jp (ix)")
                            routine.append( "; routine takes"+str(ts)+"tstates")
        
                    else:
                        if VERTICALCOMPARE and (testy != y):
                            if testy > y:
                                routine.append( "ld a,h" )
                                ts += 4
                                routine.append( "cp " + str(128+VERTICALCOMPARE/2 - 1) )
                                ts += 8
                                routine.append( "jr c, "+uid+"y_std"+str(y)+"_"+str(testy))
                                ts += 12

                                # assume ts is for a fully drawn sprite, don't add these bits in the skipped portion

                                routine.append( "bit 7,l" )

                                routine.append( "jr z, "+uid+"y"+str(y)+"_"+str(y+1) )
        
                                if y > 0:
                                    routine.append( "ld a,l" )
                                    routine.append( "add 128 + ("+uid+"y"+str(y-1)+"_x - " +str (lastx)+")/2" )
                                    routine.append( "ld l,a" )
    
                                    routine.append( "jp "+uid+"y"+str(y-1) )
                                else:
                                    routine.append( "scf" )
                                    routine.append( "jp "+uid+"finishup" )

                                    
                                routine.append( uid+"y"+str(y)+"_"+str(y+1) +":" )

                                routine.append( "ld a,l" )
                                routine.append( "add 128 + ("+uid+"y"+str(y+1)+"_x - " +str (lastx)+")/2" )
                                routine.append( "ld l,a" )

                                routine.append( "jp "+uid+"y"+str(y+1) )

                            routine.append( uid+"y_std"+str(y)+"_"+str(testy)+":")



                        if testy%2 != y%2:
                            routine.append( "ld a,l")
                            ts += 4
                            routine.append( "add 128")
                            ts += 8
                            routine.append( "ld l,a")
                            ts += 4
                            routine.append( "ld a,h")
                            ts += 4
                            routine.append( "adc 0")
                            ts += 8
                            routine.append( "ld h,a")
                            ts += 4
                            
                            y += 1
                            
                        
                        if testy > y:
                            if (testy - y) <= 6:
                                while testy != y:
                                    routine.append( "inc h")
                                    ts += 4
                                    y += 2
                            else:
                                routine.append( "ld a,"+str((testy - y)/2))
                                ts += 8
                                routine.append( "add h")
                                ts += 4
                                routine.append( "ld h,a")
                                ts += 4
                                y = testy
                        elif testy < y:
                            if (y - testy) <= 6:
                                while testy != y:
                                    routine.append( "dec h")
                                    ts += 4
                                    y -= 2
                            else:
                                routine.append( "ld a,"+str(256 - (y - testy)/2))
                                ts += 8
                                routine.append( "add h")
                                ts += 4
                                routine.append( "ld h,a")
                                ts += 4
                                y = testy

        
                        if testx > x:
                            if (testx - x) <= 6:
                                while testx != x:
                                    routine.append( "inc l")
                                    ts += 4
                                    x += 2
                            else:
                                routine.append( "ld a,"+str((testx - x)/2))
                                ts += 8
                                routine.append( "add l")
                                ts += 4
                                routine.append( "ld l,a")
                                ts += 4
                                x = testx
                        elif testx < x:
                            if (x - testx) <= 6:
                                while testx != x:
                                    routine.append( "dec l")
                                    ts += 4
                                    x -= 2
                            else:
                                routine.append( "ld a,"+str(256 - (x - testx)/2))
                                ts += 8
                                routine.append( "add l")
                                ts += 4
                                routine.append( "ld l,a")
                                ts += 4
                                x = testx


                        if VERTICALCOMPARE and (lasty != y):
                            routine.append( uid+"y"+str(y)+":" )
                            routine.append( uid+"y"+str(y)+"_x: equ "+str(x))


                literals = [0] * 256
                
                matchliteral = re.compile(r"(\A[^:\|]*[\s,])([0-9]+)\Z")
                for l in routine:
                    m = matchliteral.search(l)
                    if m:
                        b = int(m.group(2))
                        if b<256:
                            literals[b] += 1

                values = []
                for l in range(256):
                    values.append( (literals[l], l) )
                values.sort()
                values.reverse()

                
                subst = {}
                
                if values[0][0] > 0 and not BACKGROUNDCLIPPING:
                    b = values[0][1]
                    c = values[1][1]
                
                    sourcecode.append("LD bc," + str(256*b + c))
                    subst[b] = "b"
                    subst[c] = "c"
                
                if NOBACKGROUND and values[2][0] > 0:
                    d = values[2][1]
                    e = values[3][1]
                
                    sourcecode.append("LD de," + str(256*d + e))
                    subst[d] = "d"
                    subst[e] = "e"
                

                for l in routine:
                    m = matchliteral.match(l)
                    if m:
                        b = int(m.group(2))
                        if subst.has_key(b):
                            sourcecode.append(m.group(1) + subst[b])
                        else:
                            sourcecode.append(l)
                        
                        
                    else:
                        sourcecode.append(l)
        
                
                print "At halfway, storebackgroundreg =",storebackgroundreg,", pixelsstored =", len(pixelsstored)
    
    
                if SPRITEMEMORY and MEMORYPAGE:

                    sourcecode.append( "    IF $>16384")
                    sourcecode.append( "        org $-16384")
                    sourcecode.append( "        @PAGE: EQU @-PAGE + 1")
                    sourcecode.append( "        ENDIF")    
    
                if not NOBACKGROUND:
        
                    uid = "REMOVE"+key
    
                    mask = ""
                    for y in range(height):
                        for x in range(width):
                            if (sprite(y,x+offset)!=BLANKCOLOUR) or (sprite(y,x+offset+1)!=BLANKCOLOUR):
                                mask+='1'
                            else:
                                mask+='0'
    
                    if mask in drawn_masks.keys():
                        equuid = drawn_masks[mask]
    
                        print "Matched mask for "+uid+", reusing "+equuid+" remove routine."
    
                        sourcecode.append( uid+": EQU "+equuid  )  
                        sourcecode.append( uid+"PAGE: EQU "+equuid+"PAGE"  )  
                        
    
                    else:
                        drawn_masks[mask] = uid
    
                        
                        sourcecode.append( uid+":"  )  
                        sourcecode.append( uid+"PAGE: EQU @-PAGE"  )  
    
                        ts = 0
                        
                        # assume this routine will be called within low memory with the screen in high memory
                        # HL is the address to draw into
                            # assume all registers will be corrupt:
                        
                            # use DE for storing screen bytes which get pushed
                            # use bc for anding at screen edges, or possibly storing data in time
                        
                        
                        x= offset
                        y=1
                        dx = 2
                        dy = 2
                        
                        pixelsretreived = []
            
                        
                        
                        
                        sourcecode.append("pop hl")
                        ts += 12
            
                        if storebackgroundreg:
                            sourcecode.append("pop de")
                            ts += 12
                            numpops += 1
                        
            
                        if VERTICALCOMPARE:
                            sourcecode.append( "jp c, "+uid+"y0" )
                            ts += 12
    
                        
                        
    
                        b=-1
                        c=-1
                        
                        firstnavigate=True
                        
                        finished = 0
                        while not finished:
                
                            if (sprite(y,x)!=BLANKCOLOUR) or (sprite(y,x+1)!=BLANKCOLOUR):
                            
                                firstnavigate = False
                            
                                if not storebackgroundreg:
                                    sourcecode.append("pop de")
                                    ts += 12
                                    numpops += 1
                                    sourcecode.append("ld (hl),e")
                                    ts += 8
                                    pixelsretreived.append((x,y))
                                    
                                else:
                                
                                    sourcecode.append("ld (hl),d")
                                    ts += 8
                                    pixelsretreived.append((x,y))
                                    
                                    
                                
                                storebackgroundreg = (storebackgroundreg + 1) % 2
                                
                           
                            lastx, lasty = x,y
                            testx, testy, finished = navigate (sprite, x, y ,1)
                    
                            if finished:
                                if VERTICALCOMPARE:
                                    sourcecode.append(uid+"finishup:")
            
                                print "Finished, pixelsretreived =", len(pixelsretreived)
                                
                                anerror = 0
                                
                                for p in pixelsretreived:
                                    if not p in pixelsstored:
                                        print "retrieved pixel not stored at",p
                                        anerror = 1
                            
                                for p in pixelsstored:
                                    if not p in pixelsretreived:
                                        print "stored pixel not retrieved at",p
                                        anerror = 1
                        
                                if anerror:
                                    print pixelsretreived    
            
                            
                            
                                if storebackgroundreg:
                                    print "**** ERROR: something gone wrong in sprite navigation, pixels left"
                                
                                
                                sourcecode.append( "ret")
                                sourcecode.append( "; routine takes"+str(ts)+"tstates")
                
                            elif firstnavigate:
                                y = testy
                                x = testx
                
                
                            else:
                                if VERTICALCOMPARE and (testy != y):
                                    if testy > y:
                                        sourcecode.append( "ld a,h" )
                                        ts += 4
                                        sourcecode.append( "cp " + str(128+VERTICALCOMPARE/2 - 1) )
                                        ts += 8
                                        sourcecode.append( "jr c, "+uid+"y_std"+str(y)+"_"+str(testy))
                                        ts += 12
        
                                        # assume ts is for a fully drawn sprite, don't add these bits in the skipped portion
        
                                        sourcecode.append( "bit 7,l" )
        
                                        sourcecode.append( "jr z, "+uid+"y"+str(y)+"_"+str(y+1) )
                
                                        if y > 0:
                                            sourcecode.append( "ld a,l" )
                                            sourcecode.append( "add 128 + ("+uid+"y"+str(y-1)+"_x - " +str (x)+") /2" )
                                            sourcecode.append( "ld l,a" )
            
                                            sourcecode.append( "jp "+uid+"y"+str(y-1) )
                                        else:
                                            sourcecode.append( "jp "+uid+"finishup" )
        
                                            
                                        sourcecode.append( uid+"y"+str(y)+"_"+str(y+1) +":" )
        
                                        sourcecode.append( "ld a,l" )
                                        sourcecode.append( "add 128 + ("+uid+"y"+str(y+1)+"_x - " +str (x)+") /2" )
                                        sourcecode.append( "ld l,a" )
        
                                        sourcecode.append( "jp "+uid+"y"+str(y+1) )
        
                                    sourcecode.append( uid+"y_std"+str(y)+"_"+str(testy)+":")
    
    
    
                                if testy%2 != y%2:
                                    sourcecode.append( "ld a,l")
                                    ts += 4
                                    sourcecode.append( "sub 128")
                                    ts += 8
                                    sourcecode.append( "ld l,a")
                                    ts += 4
                                    sourcecode.append( "ld a,h")
                                    ts += 4
                                    sourcecode.append( "sbc 0")
                                    ts += 8
                                    sourcecode.append( "ld h,a")
                                    ts += 4
                                    
                                    y -= 1
                                
                                if testy > y:
                                    if (testy - y) <= 6:
                                        while testy != y:
                                            sourcecode.append( "inc h")
                                            ts += 4
                                            y += 2
                                    else:
                                        sourcecode.append( "ld a,"+str((testy - y)/2))
                                        ts += 8
                                        sourcecode.append( "add h")
                                        ts += 4
                                        sourcecode.append( "ld h,a")
                                        ts += 4
                                        y = testy
                                elif testy < y:
                                    if (y - testy) <= 6:
                                        while testy != y:
                                            sourcecode.append( "dec h")
                                            ts += 4
                                            y -= 2
                                    else:
                                        sourcecode.append( "ld a,"+str(256 - (y - testy)/2))
                                        ts += 8
                                        sourcecode.append( "add h")
                                        ts += 4
                                        sourcecode.append( "ld h,a")
                                        ts += 4
                                        y = testy
                
                                if testx > x:
                                    if (testx - x) <= 6:
                                        while testx != x:
                                            sourcecode.append( "inc l")
                                            ts += 4
                                            x += 2
                                    else:
                                        sourcecode.append( "ld a,"+str((testx - x)/2))
                                        ts += 8
                                        sourcecode.append( "add l")
                                        ts += 4
                                        sourcecode.append( "ld l,a")
                                        ts += 4
                                        x = testx
                                elif testx < x:
                                    if (x - testx) <= 6:
                                        while testx != x:
                                            sourcecode.append( "dec l")
                                            ts += 4
                                            x -= 2
                                    else:
                                        sourcecode.append( "ld a,"+str(256 - (x - testx)/2))
                                        ts += 8
                                        sourcecode.append( "add l")
                                        ts += 4
                                        sourcecode.append( "ld l,a")
                                        ts += 4
                                        x = testx
    
                                if VERTICALCOMPARE and (lasty != y):
                                    sourcecode.append( uid+"y"+str(y)+":" )
                                    sourcecode.append( uid+"y"+str(y)+"_x: equ "+str(x))
                
                    print numpushes, numpops

    if sourcecode:

        if SPRITEMEMORY:
            sourcecode.append( inputfile.split('/')[-1]+"ENDPAGE: EQU @-PAGE"  )  


        f = open(inputfile+".sprite.z80s", 'wb')
        for s in sourcecode:
            for c in s+"\n":
                f.write(c)
        f.close()
        
