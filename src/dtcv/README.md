# Downtown Computer Vision package

This is a support module for building the `sandiegodata.org-downtown_cv`
dataset. See the [dataset documentation]
(https://data.sandiegodata.org/dataset/sandiegodata-org-downtown-cv/) for
details about the package. You probably want to use the data package, rather
than this module.

## Description

The ``dtcv`` module has code for:

* Downloading JSON annotation files from S3 
* Downloading map image files from S3
* Extracting GCP ( ground control points ) from VIA jSON files
* Extracting count handwritten marks annotations from VIA JSON files. 
* Processing map images

