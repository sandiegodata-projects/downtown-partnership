from pathlib import Path

for f in Path('/Users/eric/Google Sync/sandiegodata.org/Projects/Downtown Partnership Homeless/processed_images/Round 2').glob('*'):
    new_name = f.name.replace(' ','-')
    print(new_name, f.parent.joinpath(new_name))
    f.rename(f.parent.joinpath(new_name))