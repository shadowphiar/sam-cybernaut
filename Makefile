ASMFLAGS = 

pyz80 = ../pyz80/pyz80.py $(ASMFLAGS)
sampalette = scripts/sampalette.py -q -o _build
dskextract = scripts/dskextract.py -o _build
sfx = scripts/sfx.py

PAL = -p 0,7,15,120,127,10,34,44,106,5,13,88,75,12,4,25

all: cybernaut.dsk cybernaut-dist.dsk

clean:
	rm -rf _build cybernaut.dsk cybernaut-dist.dsk

run: cybernaut.dsk
	open $<

run-dist: cybernaut-dist.dsk
	open $<


_build/mkdir:
	mkdir -p _build
	touch _build/mkdir


OBJ = _build/data.obj _build/data.sym _build/stereotable.o

SOURCE = src/cybernaut.z80s  \
		src/discops.z80s \
		ext/ptplayer.z80s \
		src/global.z80s \
		src/screenfunctions.z80s \
		src/specialscreencpfns.z80s \
		src/physics.z80s \
		src/config.z80s \
		src/mainmenu.z80s \
		src/menu_star_effect.z80s \
		_build/level1.z80s \
		_build/tile_properties.z80s \
		_build/sfx.inc \
		


DATA = _build/menu.png.samscreen.mdat.gz \
	_build/hector.32k.gz \
	_build/maaora.32k.gz \
	_build/ship.png_1_2.sprite.z80s \
	_build/tiles.png_15_11.sprite.z80s \
	_build/explosion.png_7.sprite.z80s \
	_build/enemy1.png_5_1.sprite.z80s \
	_build/lasershot.png_1.sprite.z80s \
	_build/rockets.png_3_1.sprite.z80s \
	_build/shots.png_11.sprite.z80s

cybernaut.dsk: $(SOURCE) $(OBJ) _build/data.sym _build/mkdir
	date +%Y-%m-%d > _build/version
	echo "(`git rev-parse --short HEAD`)" >> _build/version
	$(pyz80) -o $@ --importfile=_build/data.sym $<


_build/AUTOcybe.O.gz: cybernaut.dsk
	$(dskextract) -x AUTOcybe.O $<
	gzip -f -9 _build/AUTOcybe.O
	
cybernaut-dist.dsk: src/selfextract.z80s _build/AUTOcybe.O.gz
	$(pyz80) -o $@ $<

_build/screenfunctions.sym: _build/screenfunctions.obj

_build/screenfunctions.obj: src/screenfunctions.z80s src/global.z80s _build/mkdir
	 $(pyz80) --obj=$@ --exportfile=_build/screenfunctions.sym $<


_build/data.sym: _build/data.obj
	
_build/data.obj: src/data.z80s $(DATA) _build/font_sm.sym src/global.z80s
	 $(pyz80) --obj=$@ --importfile=_build/font_sm.sym --exportfile=_build/data.sym $<



_build/stereotable.o: src/stereotable.z80s _build/mkdir
	$(pyz80) --obj $@ $<



_build/font_sm.sym: _build/font_sm.o
_build/font_sm.o: _build/font_sm.png_31_1.sprite.z80s _build/screenfunctions.sym
	$(pyz80) --obj $@ --importfile=_build/screenfunctions.sym --exportfile=_build/font_sm.sym $<

_build/font_sm.png_31_1.sprite.z80s: graphics/font_sm.png _build/mkdir
	$(sampalette) $(PAL) -m -s -c -a -x 32 -y 2 -b 48 -S -X $<



_build/level1.z80s: maps/level1.json scripts/parselevel.py _build/mkdir 
	 scripts/parselevel.py < $< > $@

_build/tile_properties.z80s: maps/level1.json scripts/parselevel.py _build/mkdir 
	 scripts/parselevel.py --properties < $< > $@



_build/menu.png.samscreen.mdat.gz: graphics/menu.png _build/mkdir
	$(sampalette) -p 0,7,15,120,127 $<






_build/maaora.32k.gz: music/music.dsk _build/mkdir
	$(dskextract) -x maaora.32k $<
	gzip _build/maaora.32k

_build/hector.32k.gz: music/music.dsk _build/mkdir
	$(dskextract) -x hector.32k $<
	gzip _build/hector.32k






_build/ship.png_1_2.sprite.z80s: graphics/ship.png _build/mkdir
	$(sampalette) $(PAL) -s -D -1 -b 48 -x 2 -y 3 $<

_build/explosion.png_7.sprite.z80s: graphics/explosion.png _build/mkdir
	$(sampalette) $(PAL) -s -D -1 -b 0 -x 8 $<

_build/lasershot.png_1.sprite.z80s: graphics/lasershot.png _build/mkdir
	$(sampalette) $(PAL) -s -D -1 -b 0 -y 2 $<

_build/rockets.png_3_1.sprite.z80s: graphics/rockets.png _build/mkdir
	$(sampalette) $(PAL) -s -D -1 -a -b 48 -x 4 -y 2 $<

_build/enemy1.png_5_1.sprite.z80s: graphics/enemy1.png _build/mkdir
	$(sampalette) $(PAL) -s -D -1 -b 48 -x 6 -y 2 $<

_build/shots.png_11.sprite.z80s: graphics/shots.png _build/mkdir
	$(sampalette) $(PAL) -s -D -1 -b 0 -y 12 $<

_build/tiles.png_15_11.sprite.z80s: graphics/tiles.png _build/mkdir
	$(sampalette) $(PAL) -s -D -c -a -x 16 -y 12 -b 48 $<



_build/sfx.inc: music/music.dsk ../scripts/sfx.py _build/mkdir
	$(dskextract) -x EFFECTS.M $<
	$(sfx) < _build/EFFECTS.M > _build/sfx.inc




