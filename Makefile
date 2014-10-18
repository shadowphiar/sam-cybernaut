ASMFLAGS = 

pyz80 = ../pyz80/pyz80.py $(ASMFLAGS)
sampalette = scripts/sampalette.py -q -o _build
dskextract = scripts/dskextract.py -o _build


PAL = -p 0,7,15,120,127,10,34,44,106,5,13,88,75,12,4,25

all: cybernaut.dsk

clean:
	rm _build/*

run: cybernaut.dsk
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
		_build/level1.z80s \


DATA = _build/menu.png.samscreen.mdat.gz \
	_build/hector.32k.gz \
	_build/maaora.32k.gz \
	_build/ship.png_1_2.sprite.z80s \
	_build/tiles.png_15_11.sprite.z80s \
	


cybernaut.dsk: $(SOURCE) $(OBJ) _build/data.sym _build/mkdir
	date +%Y-%m-%d > _build/version
	echo "(`git rev-parse --short HEAD`)" >> _build/version
	$(pyz80) -o $@ --importfile=_build/data.sym $<







_build/screenfunctions.obj: src/screenfunctions.z80s src/global.z80s
	 $(pyz80) --obj=$@ --exportfile=_build/screenfunctions.sym $<


_build/data.sym: _build/data.obj
	
_build/data.obj: src/data.z80s $(DATA) _build/font_sm.sym src/global.z80s
	 $(pyz80) --obj=$@ --importfile=_build/font_sm.sym --exportfile=_build/data.sym $<



_build/stereotable.o: src/stereotable.z80s
	$(pyz80) --obj $@ $<



_build/font_sm.sym: _build/font_sm.o
_build/font_sm.o: _build/font_sm.png_31_1.sprite.z80s _build/screenfunctions.sym
	$(pyz80) --obj $@ --importfile=_build/screenfunctions.sym --exportfile=_build/font_sm.sym $<

_build/font_sm.png_31_1.sprite.z80s: graphics/font_sm.png
	$(sampalette) $(PAL) -m -s -c -a -x 32 -y 2 -b 48 -S -X $<



_build/level1.z80s: maps/level1.json scripts/parselevel.py
	 scripts/parselevel.py < $< > $@




_build/menu.png.samscreen.mdat.gz: graphics/menu.png
	$(sampalette) -p 0,7,15,120,127 $<






_build/maaora.32k.gz: music/music.dsk
	$(dskextract) -x maaora.32k $<
	gzip _build/maaora.32k

_build/hector.32k.gz: music/music.dsk
	$(dskextract) -x hector.32k $<
	gzip _build/hector.32k








_build/ship.png_1_2.sprite.z80s: graphics/ship.png
	$(sampalette) $(PAL) -s -D -1 -b 48 -x 2 -y 3 $<




_build/tiles.png_15_11.sprite.z80s: graphics/tiles.png
	$(sampalette) $(PAL) -s -c -a -x 16 -y 12 -b 48 $<







