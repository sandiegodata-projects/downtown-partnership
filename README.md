# Counting San Diego Homeless


## Running Updates

First, install the ``dtcv`` package in ``src/dtcv``

```bash
pip install -e src/dtcv
```

Unpack your files for your update into one of the update directories, 
like ``update-2024``. The directory should have your files in it in the 
same format as the other directories in ``update-2022``, for instance:

```
update-2022/SDDT_092623
├── count
├── gcp
├── gcp-errors
├── intersection.csv
└── output
```

* ``count`` has all of the JSON files for the counts that were saved out of VIA
* ``gcp`` has all of the GCP files saved outof VIA
* ``intersection.csv`` lists your GCP intersections. 

The ``gcp-errors`` and ``output`` directories are created by the programs. 


To process the files, run these programs: 

```bash
dt_process -v -i intersection.csv -c count output
dt_process -v -i intersection.csv -g gcp output
dt_process --final output
```


