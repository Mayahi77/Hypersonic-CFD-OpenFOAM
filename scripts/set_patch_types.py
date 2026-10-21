"""Set Gmsh-imported patch types without changing face addressing."""
import re
import sys
from pathlib import Path
path = Path(sys.argv[1])
s = path.read_text()
for name, kind in [('wedgeFront', 'wedge'), ('wedgeBack', 'wedge'), ('cylinderWalls', 'wall')]:
    s, count = re.subn(r'(\b' + name + r'\s*\{[^{}]*?\btype\s+)\w+(\s*;)',
                       lambda m: m[1] + kind + m[2], s, flags=re.S)
    if count != 1:
        raise ValueError('Expected exactly one patch: ' + name)
path.write_text(s)
