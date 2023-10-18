# Counting San Diego Homeless



The ``source_files`` director holds all of the source PDFs. images are extracted from them with the ``dsdp_extract``
program. The program builds the set of images in the ``images`` directory.

The ``dsdp_text`` program tries to read the images to determine what the neighborhood name is. It will also rotate
the image and move the rotated, renamed images to the ``process_images`` directory.
