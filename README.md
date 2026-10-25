# Document Scanner (IPCV Mini Project)

Turns a phone photo of a page into a clean, flat, top-down scan, like CamScanner.
Built with Python, OpenCV and NumPy only, with no machine learning involved.

## Project structure

```
doc_scanner/
├── app.py                # Streamlit web frontend
├── main.py               # command-line entry point
├── requirements.txt
├── samples/              # put input photos here
├── output/               # scans are written here
└── scanner/
    ├── __init__.py
    ├── pipeline.py       # DocumentScanner: runs all steps in order
    ├── preprocessing.py  # resize, grayscale, blur, Canny edges
    ├── detection.py      # find the page (largest 4-corner contour)
    ├── transform.py      # corner ordering + perspective warp
    ├── enhance.py        # B&W / gray / colour scan filters
    └── utils.py          # image I/O, step visualisation
```

## Setup

```bash
pip install -r requirements.txt
```

## Web app

```bash
streamlit run app.py
```

Features:
- Upload one or more photos, use the camera, or try the built-in samples
- Four scan modes: Black & White, Grayscale, Magic Colour, Original
- Detected outline shown next to the scan, with a step-by-step view of the processing
- Rotate each page
- Download each page as PNG, or all pages as one PDF

### Hosting (Streamlit Community Cloud, free)
1. Push this folder to a public GitHub repository.
2. Sign in at https://share.streamlit.io with GitHub.
3. Click **Create app**, choose the repo and branch, and set the main file to `app.py`.
4. Deploy. You get a public `https://<name>.streamlit.app` link.

## Command-line usage

```bash
python main.py samples/page.jpg                     # black & white scan
python main.py samples/page.jpg --mode color        # colour scan
python main.py samples/page.jpg --steps --show      # save + show every step
```

Modes: `bw` (default), `gray`, `color`, `original`.
Other options: `--rotate 90|180|270` and `--pdf` (also save a PDF).

`--show` needs the desktop OpenCV build (`pip install opencv-python`), because
the requirements use the headless build so the app can be hosted.

## How it works (and syllabus mapping)

| # | Step | OpenCV | Syllabus experiment |
|---|------|--------|---------------------|
| 1 | Resize + grayscale | `resize`, `cvtColor` | 8. Image assessment |
| 2 | Gaussian blur | `GaussianBlur` | 2. Smoothing filters |
| 3 | Edge detection + closing | `Canny`, `morphologyEx` | 5. Edge detection, 6. Morphology |
| 4 | Find page outline | `findContours`, `approxPolyDP` | 7. Object detection |
| 5 | Perspective warp | `getPerspectiveTransform`, `warpPerspective` | 9. Image transformation |
| 6a | B&W scan | `adaptiveThreshold` | 1. Thresholding |
| 6b | Gray scan | CLAHE | 3. Histogram modelling |
| 6c | Colour scan | CLAHE + unsharp mask | 2. Sharpening, 11. Arithmetic ops |

A candidate outline is accepted only if it covers at least 20% of the photo
and is clearly brighter than its surroundings, so boxes printed on a page
are not mistaken for the page itself. If no page outline is found, the whole image is used as the page and the
filters are still applied.

## Test images
`samples/internet/` holds test photos taken from the
[andrewdcampbell/OpenCV-Document-Scanner](https://github.com/andrewdcampbell/OpenCV-Document-Scanner)
repository. Run them all with:

```bash
for f in samples/internet/*; do python main.py "$f" -o output/internet --steps; done
```

## Tips for good results
- Place the page on a contrasting (darker) background.
- Keep all four corners of the page in the photo.
- Avoid strong glare on the page.
