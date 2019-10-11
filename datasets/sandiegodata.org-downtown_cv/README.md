# Downtown Homeless Computer Vision Package

This dataset collects records related to a conversion of 5 years of paper maps
that record positions of homeless sleepers in downtown San Diego. The San Diego
Regional Data Library is [converting these paper maps to a digital
form](http://downtown-homelessness.sandiegodata.org/) with a manual process that
uses an image annotation tool, and theses annotations can be used to train
computer vision algorithms to georeference maps and recognize handwritten marks.

These datasets link to map urls and annotations, for three kinds of annotations:

* Ground Control Points, which identify the map image locations for known intersections, linking image coordinates ( in pixels ) to geographic coordinates.
* Image locations of handwritten marks and the number written in the mark.
* File annotations, for other handwritten notes such as the temperature and presence of rain. 

## More Information:

* [Blog Post](https://www.sandiegodata.org/2019/09/computer-vision-for-greater-good/). For more discussion about the GCP and handwritten marks, and the tasks in volved
in developing computer vision algorithms for these data, see our recent blog
post on the subject.
* [Clustering Notebook](https://nbviewer.jupyter.org/github/sandiegodata-projects/downtown-partnership/blob/master/datasets/sandiegodata.org-downtown_cv/notebooks/Template%20Matching%20Clusters.ipynb). For some examples of using OpenCV to extract and match templates, to georeference maps, see the Templates and Clustering Jupyter Notebook].
* [Extract Marks Notebook](https://nbviewer.jupyter.org/github/sandiegodata-projects/downtown-partnership/blob/master/datasets/sandiegodata.org-downtown_cv/notebooks/Extract%20Marks.ipynb). For examples of extracting ( but not recognizing ) handwritten marks, see this notebook. 


## Developer notes

To build this package, the ``dtcv`` package must be installed, from the ``lib`` directory at the root of the repository.

    $  pip install -e ../../lib/dtcv/

After anotation JSON files are copied into S#, the list of S# urls must be
updated. To refresh the list of urls run

    $  bin/update_s3.sh <s3-profile>

