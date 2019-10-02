## Building the package

To build the data, install the ``dtcv`` package from the
[``downtown-partnership``](https://github.com/sandiegodata-projects/downtown-par
tnership) repository, then run ``dt_process`` to create data in the data
directory. The source directory for the ``dt_process`` program should have all
of the completed GCP and Count annotation files for VIA. The offical set of
these files is stored in a [Google Drive
folder.](https://drive.google.com/drive/u/3/folders/1RtVVir41bemSNIfQkSOMtT9LAlA
cmVcN)

To build the data files from the VIA annotation files: 

    $ pip install -e ../../src/dtcv
    $ dt_process <annotations_dir> data

This will produce these files: 

* counts.csv
* files.csv
* gcp_transforms.csv
* raw_count_annotations.csv
* raw_file_annotations.csv
* raw_gcp.csv

Only the ``counts.csv`` and ``files.csv`` files are incorporated into this package. 
