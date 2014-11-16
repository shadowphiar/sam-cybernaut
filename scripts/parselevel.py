#!/usr/bin/env python

import json, sys

tl = json.loads(sys.stdin.read())

tilelayers = [ x for x in tl['layers'] if x["type"]=="tilelayer"]
objects = { z['name']:z for z in x['objects'] for x in tl['layers'] if x["type"]=="objectgroup"}

tileproperties = [ x for x in tl['tilesets'] if x["name"]=="tiles"][0]["tileproperties"]
tile = [ tileproperties[str(k)].keys() if tileproperties.has_key(str(k)) else [] for k in range(256) ]


if '--properties' in sys.argv:
    properties = set([ a for t in tile for a in t  ])

    b=1
    for p in properties:
        print "TILE_"+p+": equ "+str(b)
        b <<= 1
    print ""    
    for t in range(256):
        print "tile_properties_"+str(t)+": equ "+( '+'.join(['TILE_'+x for x in tile[t]]) if tile[t] else '0')

    sys.exit(0)


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
        sprites = []
        for y in range(11):
            n = (j*11+y)*w + i*16
            for x in range(16):
                room.append( max (0, int(l['data'][ n+x ]) - 1) )            

    
        for y in range(11):        
            for x in range(16):
                if room[16*y+x] in (17,18,19,20):
                    s = y
                    while (s > 0) and 'COLLIDES' not in tile[room[16*(s-1)+x]]:
                        s -= 1 
                
                    sprites.append("    DB 2,"+str(16*x)+","+str(16*s)+",0,16,"+str((y-s+1)*16))
                    sprites.append("    DW STATIC_ROCKET_FRAME, STATIC_ROCKET_COLLIDE, UP_ROCKET_TILES,"+str((100*(x+y)) % 1024)+",30,"+str(256*(256-(y-s)*16))+",0")
                                                                            
                elif room[16*y+x] in (44,45,46,47):
                    s = y
                    while (s < 10) and 'COLLIDES' not in tile[room[16*(s+1)+x]]:
                        s += 1
                    sprites.append("    DB 2,"+str(16*x)+","+str(16*y)+",0,16,"+str((s-y+1)*16))
                    sprites.append("    DW STATIC_ROCKET_FRAME, STATIC_ROCKET_COLLIDE, DOWN_ROCKET_TILES,"+str((100*(x+y)) % 1024)+",30,0,0")
            
            
            
        assert len(room) == 16*11
        if max(room) > 1:
            roomindex[(j,i)] = len(rooms) * (16*11)
            rooms.append( "  @d"+str(j)+"_"+str(i)+":     DB " + ','.join([str(d) for d in room]))
            rooms.extend(sprites)
            rooms.append( "    db 255 ; objects end")
        

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
    row = [ ("@d"+str(j)+"_"+str(i)) if roomindex.has_key((j,i)) else "0"  for i in range(w/16) ]
    print "    DW "+ ', '.join(row)
    
print "@data:"

for r in rooms:
    print r








