#!/usr/bin/env python

import json, sys

tl = json.loads(sys.stdin.read())

tilelayers = [ x for x in tl['layers'] if x["type"]=="tilelayer"]
objects = { z['name']:z for z in x['objects'] for x in tl['layers'] if x["type"]=="objectgroup"}

assert len(tilelayers) == 1
l = tilelayers[0]

w= l['width']
h= l['height']


assert w % 16 == 0
assert h % 11 == 0

rooms = []
roomindex = {}

for j in range(h/11):
    for i in range(w/16):
        room = []
        for y in range(11):
            n = (j*11+y)*w + i*16
            room.extend( l['data'][ n : n+16 ] )
        assert len(room) == 16*11
        if max(room) > 1:
            roomindex[(j,i)] = len(rooms) * (16*11)
            rooms.append( "    DB " + ','.join([str(d-1 if d>0 else 0) for d in room]))
        

startx = objects["start"]["x"] / 16
starty = objects["start"]["y"] / 16


print " DS ALIGN 256"
print "    DB "+str(w/16)+" ; width"
print "    DB "+str(h/11)+" ; height"

print "    DW @offsets+2*"+str(w*(starty/11)+(startx/16))+"; player starts in room"
print "    DB "+str(16*(starty%11))+"; player starts y"
print "    DB "+str(16*(startx%16))+"; player starts x"

print "@offsets:"

for j in range(h/11):
    row = [ "@data + "+str(roomindex[(j,i)]) if roomindex.has_key((j,i)) else "0"  for i in range(w/16) ]
    print "    DW "+ ', '.join(row)
    
print "@data:"

for r in rooms:
    print r








