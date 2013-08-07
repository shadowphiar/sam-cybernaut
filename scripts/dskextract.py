#!/usr/bin/env python

import sys, os, getopt, gzip
from os import path

def help():
    print """Usage:
skextract.py [options] imagefile
-x=name     extract named file
-o=dir      specify output directory"""

def log(*args):
    if verbosity < 1:
        return

    strargs = []
    for a in args:
        strargs.append(str(a))
    sys.stderr.write( ' '.join(strargs) + '\n' )



class dsk:
    def __init__(self, filename=None):
        self.filename = filename
    
        if (filename==None):
            self.data = '\0' * 819200
        else:
            log ("Loading diskimage from", filename)
            f = gzip.GzipFile(filename, 'rb')        
            self.data = f.read()    
            f.close()

        if len(self.data) != 819200:
            help()
            sys.exit(1)
        

    def read_at(self, track, sector):
        if not 1 <= sector <= 10:
            log ("Invalid sector number", sector)
            raise ValueError
    
        raw_sector = sector - 1
        if track >= 128:
            if not 128 <= track <= 207:
                log ("Invalid track number", sector)
                raise ValueError
            raw_track = track-128
            raw_side = 1
        else:
            if not 0 <= track <= 79:
                log ("Invalid track number", sector)
                raise ValueError
            raw_track=track
            raw_side = 0

        datap = (raw_track*20+raw_side*10+raw_sector)*512
        return self.data[datap:datap+512]



    def extract(self, filename, odir=""):
        filename = (filename + ' '*10)[:10]
    
        # search the directory for matching filename
        for index in range(80):
            direntry = self.read_at( index/20, (index%20)/2 + 1 ) [(index%2)*256 : (index%2)*256 + 256 ] 
            if (direntry[1:11] == filename) and (ord(direntry[0]) != 0):
                break
        else:
            log ("Could not find", filename, "on this image!")
            raise IOError

        flength = ord(direntry[239]) * 16384 + ord(direntry[241]) * 256  + ord(direntry[240])
        header = 9
        log ("Reading", flength, "bytes from", filename )

        track = ord(direntry[13])
        sector= ord(direntry[14])

            
        output = open( path.join(odir, filename.rstrip() ), "wb")
        
        
        while flength > 0:
            s_data = self.read_at(track, sector)
            output.write( s_data[ header : min(510, flength) ] )
            flength -= (510 - header)
            header = 0
            track = ord ( s_data[510] )        
            sector = ord ( s_data[511] )        
        
        output.close()
    



command = []
odir = ""
verbosity = 1

option_args, file_args = getopt.getopt(sys.argv[1:], 'ho:x:vq', ['help'])

if len(file_args) != 1:
    help()
    sys.exit(1)


for option,value in option_args:
    if option in ['-h', '--help']:
        help()
        sys.exit(0)

    if option in ['-o']:
        odir = value

    if option in ['-x']:
        command.append( ('-x',value) )

    if option in ['-q']:
        verbosity = 0

    if option in ['-v']:
        verbosity += 1

if len(command) == 0:
    help()
    sys.exit(1)

DSK = dsk(file_args[0])
    
for option,value in command:
    if option in ['-x']:
        DSK.extract(value, odir)








