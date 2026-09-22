"""W24 slice: drop DEAD ^Warhead_ inherits on a WHITELIST of weapons, then drop only the
removal lines that become orphans ON THOSE SAME WEAPONS. Verified behaviour-preserving:
the resolved node of all ~3000 weapons must be byte-identical afterwards."""
import sys, json, collections, pathlib
sys.path[:0]=['tools/audit']; sys.stdout.reconfigure(encoding='utf-8')
import miniyaml
ROOT = pathlib.Path(".").resolve()

def snapshot(rs):
    def dump(n, ind=0):
        if n is None: return "<none>"
        out=[]
        for c in sorted(n.children, key=lambda x:(x.key, str(x.value))):
            out.append("  "*ind + f"{c.key}: {c.value}"); out.append(dump(c, ind+1))
        return "\n".join(x for x in out if x.strip())
    return {w: dump(rs.resolve_weapon(w)) for w in sorted(rs.weapons)}

def drop(by_file):
    total=0
    for f, lines_to_go in by_file.items():
        p=ROOT/f; raw=p.read_bytes().decode("utf-8")
        nl="\r\n" if "\r\n" in raw else "\n"; lines=raw.split(nl)
        for line in sorted(set(lines_to_go), reverse=True):
            del lines[line-1]; total+=1
        p.write_bytes(nl.join(lines).encode("utf-8"))
    return total

rs = miniyaml.Ruleset('.')
before = snapshot(rs)

# the whitelist: >=2 ^Warhead_ inherits, >=1 of them DEAD (its node deleted locally),
# and at least one LIVE ^Warhead_ left afterwards so the weapon keeps a warhead template.
white=[]
for w in sorted(rs.weapons):
    if w.startswith("^"): continue
    node=rs.weapon(w)
    whs=[t for _,t in rs.inherits_of(node) if t.startswith("^Warhead_")]
    if len(whs)<2: continue
    rm={c.key for c in node.children if c.key.startswith("-Warhead@")}
    dead=[t for t in whs if "-Warhead@"+t[len("^Warhead_"):] in rm]
    if dead and len(whs)-len(dead) >= 1:
        white.append(w)
EXCLUDE = set(json.load(open(sys.argv[1]))) if len(sys.argv)>1 else set()
white=[w for w in white if w not in EXCLUDE]
print(f"whitelist: {len(white)} weapons  (excluded {len(EXCLUDE)})")

lines=collections.defaultdict(list)
for w in white:
    node=rs.weapon(w)
    whs=[t for _,t in rs.inherits_of(node) if t.startswith("^Warhead_")]
    rm={c.key for c in node.children if c.key.startswith("-Warhead@")}
    dead={t for t in whs if "-Warhead@"+t[len("^Warhead_"):] in rm}
    for c in node.children:
        if (c.key=="Inherits" or c.key.startswith("Inherits@")) and c.value in dead:
            lines[c.file].append(c.line)
print("dead ^Warhead_ inherits dropped:", drop(lines))

# orphaned removal lines, WHITELIST ONLY
rs = miniyaml.Ruleset('.')
cache={}
def prov(t):
    if t not in cache:
        r=rs.resolve_weapon(t); cache[t]={c.key for c in r.children} if r else set()
    return cache[t]
lines2=collections.defaultdict(list)
for w in white:
    node=rs.weapon(w)
    if node is None: continue
    lk={c.key for c in node.children}; fp=set()
    for _,t in rs.inherits_of(node): fp |= prov(t)
    for c in node.children:
        if c.key.startswith("-") and c.key[1:] and c.key[1:] not in fp and c.key[1:] not in lk:
            lines2[c.file].append(c.line)
print("orphaned removal lines dropped:", drop(lines2))

rs = miniyaml.Ruleset('.')
after = snapshot(rs)
changed = sorted(w for w in set(before)&set(after) if before[w]!=after[w])
print(f"RESOLVED WEAPONS CHANGED: {len(changed)}")
json.dump(changed, open("C:/tmp/w2_changed.json","w"), indent=1)
for w in changed[:12]: print("   ", w)
