## Overview

We offer the Keepers photobook designer app that for our customers to create
photobooks. The app uploads the customers photos onto AWS and a lambda process
will work with lulu.com's print-on-demand API to print the photobooks and ship
them to the users.

We offer two product sizes: small_square (7.5 x 7.5 inches) and square ( 8.5 x
8.5) ; two types of covers: soft_cover and hard_cover.

In our preparation pipeline, we have already downloaded the uploaded
images and stored them in a local directory. The details of the file will be
provided in the "Keepers Spec" section.

The key file is `prepress.py`. It prepares the cover and inner pages PDF files
to ensure that they conform to Lulu's requirements.


## Lulu Specs

Lulu provides a detailed PDF guide for the cover and inner pages, which can be
found at the attached "spec/lulu-pdf-creation-guide.pdf" file. I will refer to 
this document as "the guide" in the following sections.

Please use the terms defined on the Page 9 and 10 of the guide.

### Book Cover Specifications (For a 6x9 book)

- Single page, portrait oriented layout
- Embedded images are 300 PPI resolution minimum, not exceeding 600 PPI
  resolution
- Vector images are rasterized
- All fonts are embedded
- Transparent layers and vector objects are flattened
- Pages sized to match intended trim size: Trim Size = 6 x 9 in/152.4 x 228.6
  mm Page Size = 6.25 x 9.25 in/158.75 x 234.95 mm
- A minimum 0.5 in/12.7 mm Safety Margin
- A minimum 0.2 in/2.08 mm Gutter Margin
- Do NOT include trim, bleed, or margin lines
- Do NOT use any security/password file protection

### Interior File with Bleed Specifications (For a 6x9 book)

- Page size must be 0.25 in (6.35 mm) larger in both width and height than the
  book size. Example: 6 x 9 in (152 mm x 229 mm) book requires a PDF with pages
  sized 6.25 x 9.25 in (159 mm x 235 mm).
- Interior should be output as a single-page layout, print-ready PDF with all
  pages created at the same size and orientation.
- Crop marks or registration marks should not be included.
- If your book is intended for distribution, any text within an image must be
  positioned at least 0.5 in (12.7 mm) from the edge of the finished page size.
- Although we make every effort to provide high-quality, consistently produced
  books, there can be slight variations from press to press in the trim size of
  your work. 
- Allow for a printing trim variance of 0.125 in (3.17 mm).


### Interior File with Full Bleed Specifications

- Page size must be 0.25 in (6.35 mm) larger in both width and height than the book size. 
- Example: 6 x 9 in (152 mm x 229 mm) book requires a PDF with pages sized 6.25 x 9.25 in (159 mm x 235 mm).
- Interior should be output as a single-page layout, print-ready PDF with all pages created at the same size and orientation.
- Crop marks or registration marks should not be included.
- If your book is intended for distribution, any text within an image must be positioned at least 0.5 in (12.7 mm) from the edge of the finished page size.
- Although we make every effort to provide high-quality, consistently produced books, there can be slight variations from press to press in the trim size of your work. Allow for a printing trim variance of 0.125 in (3.17 mm).


### Example Cover PDF 

Lulu provides two example cover PDFs in the "spec" directory. The files are

- `spec/8.5x8.5_hard_cover-89_pages.pdf`
- `spec/8.5x8.5_soft_cover-89_pages.pdf`


## Keepers Specs

Each order will have a unique identifier that will be passed into the
`prepress.py` script by the argument `--order-id`. The order id will be used to
create the output PDF files as `{order_id}_cover.pdf` and `{order_id}_inner.pdf`.

### Image Directory 

The predownloaded images are stored in a local directory. The directory will be
passed into the `prepress.py` script by the argument `--input-folder`. The
number of pages per book can vary.

The naming convention of the files is as follows:
- The front cover is 0.png, 
- the first page is 1.png, and so on.
- If the book has 89 pages, the last page will be 89.png. There will be no 90.png.
- The back cover will be keepers' logo located in `resources/logo.png`

### Individual Image Specs

Each page of the photobook is stored as a separate png file,
- colour profile: Adobe RGB (1998)
- resolution: 300 PPI 
- image size of 8 x 8 inches (2400 x 2400 pixels)

All image files MUST BE converted to CMYK color space 
using the colour profile. The .icc files requiired for the conversion are
provided in the `resources` directory.

All pages, including front cover, will be used as full bleed.

Please use imagemagick to upscale or downscale the images to the full bleed
size as required by Lulu. Make sure that the images are resized. We do not want
white space around the images.

### Cover PDF Specs

- The cover PDF will be a single page PDF.
- If the order is for a hard cover, the cover needs to have a wrap area of
  0.75" on all edges as described in the `spec/8.5x8.5_hard_cover-89_pages.pdf`
  file.
- Both hard and soft covers will have a spine width which is calculated
  according to the number of pages in the book. The formula is provided on Page
  14 and 15 in the guide.
- The back cover will be placed center bottom of the left page of the cover
  PDF. It'll be 0.5" high and 2" from the bottom of the trim edge.

### Inner PDF Specs

- The inner PDF will be a single PDF with all the pages in the order.
- The file will be created according to the full bleed specifications provided above.
- Try to parallelize the conversion process to speed up the process.
- Produce a progress bar to show the progress of the conversion process.


## Prepress.py

"""bash
python prepress.py \
    --order-id 28912-0 \
    --input-folder ./images \
    --output-folder ./ \
    --cover-type hard_cover \
    --book-size square \
    --process cover
"""


## Python Code Conventions

- Use Python 3.9. Use black with basic "strictMode". Do not use pyhint.
- Prefer system libraries over third-party libraries. Prefer fewer
  dependencies. Prefer popular libraries over less popular ones. For example,
  use `Pillow` over `wand` or `PyPDF2`.
- For import, put system libraries first, then third-party libraries, then
  local libraries. With one-line between each group. Use `isort` for sorting.
- Use default value for optional arguments. Document the reason to use a
  non-default value if we need to specify the argument with a non-default
  value. 
- use `logging` for logging instead of `print`. use levels properly. Use
  `logging.debug` to replace inline comments and `logging.info` to replace
  block comments that describe the main purpose of a function or a section of
  code.
