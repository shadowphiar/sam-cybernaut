ASMFLAGS = 

pyz80 = ../pyz80/pyz80.py $(ASMFLAGS)
sampalette = scripts/sampalette.py -q -o _build
dskextract = scripts/dskextract.py -o _build


PAL = 0,7,15,120,127,10,34,44,106,5,13,88,75,12,4,25

all: cybernaut.dsk

clean:
	rm _build/*

run: cybernaut.dsk
	open $<

_build/mkdir:
	mkdir _build
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


DATA = _build/menu.png.samscreen.mdat.gz \
	_build/hector.32k.gz \
	_build/maaora.32k.gz \



cybernaut.dsk: $(SOURCE) $(OBJ)  _build/mkdir
	$(pyz80) -o $@ --importfile=_build/data.sym $<







_build/screenfunctions.obj: src/screenfunctions.z80s src/global.z80s
	 $(pyz80) --obj=$@ --exportfile=_build/screenfunctions.sym $<


_build/data.sym: _build/data.obj
	
_build/data.obj: src/data.z80s $(DATA) _build/screenfunctions.obj src/global.z80s
	 $(pyz80) --obj=$@ --importfile=_build/screenfunctions.sym --exportfile=_build/data.sym $<



_build/stereotable.o: src/stereotable.z80s
	$(pyz80) --obj $@ $<












_build/menu.png.samscreen.mdat.gz: graphics/menu.png
	$(sampalette) -p 0,7,15,120,127 $<




_build/maaora.32k.gz: music/music.dsk
	$(dskextract) -x maaora.32k $<
	gzip _build/maaora.32k

_build/hector.32k.gz: music/music.dsk
	$(dskextract) -x hector.32k $<
	gzip _build/hector.32k
