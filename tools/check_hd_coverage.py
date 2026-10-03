import re, os, sys, collections

tileset_yaml = sys.argv[1]
meg_names = sys.argv[2]
folder_in_meg = sys.argv[3]  # e.g. DESERT  (the theater folder under TERRAIN)

# Build set of meg DDS basenames per template-folder: {FOLDER: max_index, count}
meg = collections.defaultdict(set)
pat = re.compile(r'TERRAIN\\' + re.escape(folder_in_meg) + r'\\([^\\]+)\\\1-(\d+)\.DDS$', re.I)
with open(meg_names) as f:
    for line in f:
        m = pat.search(line.strip())
        if m:
            meg[m.group(1).upper()].add(int(m.group(2)))

# Parse templates from tileset yaml: capture Images, Size, Categories, and Tiles indices
text = open(tileset_yaml, encoding='utf-8').read()
# split on Template@
blocks = re.split(r'\n\tTemplate@', text)
print(f"{'TEMPLATE(Images)':<22}{'Cat':<14}{'Size':<7}{'need':<6}{'megHas':<7}{'verdict'}")
for b in blocks[1:]:
    img = re.search(r'Images:\s*(\S+)', b)
    size = re.search(r'Size:\s*(\d+)\s*,\s*(\d+)', b)
    cat = re.search(r'Categories:\s*([^\n]+)', b)
    if not img:
        continue
    image = img.group(1)
    category = (cat.group(1).strip() if cat else '')
    if 'Cliff' not in category:
        continue
    w, h = (int(size.group(1)), int(size.group(2))) if size else (1, 1)
    need = w * h
    # folder key: desert keeps extension -> full filename upper
    folderkey = os.path.basename(image).upper()
    have = meg.get(folderkey, set())
    have_all = all(i in have for i in range(need))
    verdict = 'HD' if have_all else ('CLASSIC (meg idx ' + (str(sorted(have)) if have else 'NONE') + ')')
    print(f"{image:<22}{category[:13]:<14}{f'{w}x{h}':<7}{need:<6}{len(have):<7}{verdict}")
