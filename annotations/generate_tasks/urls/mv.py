from collections import defaultdict
from pathlib import Path

d = defaultdict(list)

for l in Path('all.txt').open().readlines():
    l = l.strip()
    parts = l.split('/')
    date_parts = parts[-1].split('-')
    year = date_parts[0][0:4]
    neighborhood = parts[-2]
    fn = f"{neighborhood}-{year}.txt"

    d[fn].append(l)


for k,v in d.items():
    print(k, len(v))
    with Path(k).open('w') as f:
        f.write('\n'.join(v))
