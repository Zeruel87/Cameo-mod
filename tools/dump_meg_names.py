import struct, os, re, sys

meg = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Blackrobe\Games\Steam\steamapps\common\CnCRemastered\Data\TEXTURES_RA_SRGB.MEG"
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.environ['TEMP'], 'mobius', 'ra_meg_names.txt')

with open(meg, 'rb') as f:
    head = f.read(24)
    id_, ver, hdr, nstr, nfiles, ssize = struct.unpack_from('<IIIIII', head, 0)
    print("id=%08x ver=%08x numStrings=%d numFiles=%d stringsSize=%d" % (id_, ver, nstr, nfiles, ssize))
    names = []
    for _ in range(nstr):
        ln = struct.unpack('<H', f.read(2))[0]
        names.append(f.read(ln).decode('ascii', 'replace'))

os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w') as o:
    o.write("\n".join(names))
print("wrote", out, len(names), "names")

terr = [n for n in names if 'TERRAIN' in n.upper()]
print("terrain entries:", len(terr))

theaters = {}
pat = re.compile(r'TERRAIN\\([^\\]+)\\', re.I)
for n in terr:
    m = pat.search(n)
    if m:
        theaters[m.group(1).upper()] = theaters.get(m.group(1).upper(), 0) + 1
print("theaters under TERRAIN:", sorted(theaters.items()))
