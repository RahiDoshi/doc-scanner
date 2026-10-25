"""Streamlit web frontend.

Run locally with:
    streamlit run app.py
"""

import time
from pathlib import Path

import streamlit as st

from scanner import DocumentScanner, ScanResult
from scanner.enhance import ScanMode
from scanner.utils import decode_image, encode_png, images_to_pdf, rotate, to_rgb
from ui import components as ui

SAMPLES_DIR = Path(__file__).parent / "samples" / "internet"

MODES = {
    ScanMode.BW: ("Black & White", "Crisp photocopy look, best for text"),
    ScanMode.GRAY: ("Grayscale", "Even contrast, keeps shading"),
    ScanMode.COLOR: ("Magic Colour", "Brightened and sharpened colours"),
    ScanMode.ORIGINAL: ("Original", "Flattened page, no filter"),
}

STEP_INFO = {
    "1_original": ("Original", "Input photo, resized for speed"),
    "2_grayscale": ("Grayscale", "Single intensity channel"),
    "3_blurred": ("Gaussian Blur", "Smoothing removes noise"),
    "4_edges": ("Canny Edges", "Edges + morphological closing"),
    "5_detected": ("Page Detected", "Largest 4-corner contour"),
    "6_warped": ("Perspective Warp", "Top-down view of the page"),
    "7_scanned": ("Final Scan", "Threshold / histogram equalization"),
}


@st.cache_data(show_spinner=False, max_entries=32)
def scan_bytes(data: bytes, mode: ScanMode) -> tuple[ScanResult, float]:
    """Scan an image and return the result with the time it took in seconds."""
    start = time.perf_counter()
    result = DocumentScanner(mode=mode).scan(decode_image(data))
    return result, time.perf_counter() - start


def sidebar() -> tuple[ScanMode, bool]:
    with st.sidebar:
        st.markdown("### Settings")
        mode = st.radio(
            "Scan style", list(MODES),
            format_func=lambda m: MODES[m][0],
            captions=[detail for _, detail in MODES.values()],
        )
        show_steps = st.toggle("Show processing steps", value=True)

        st.divider()
        st.markdown("### Syllabus coverage")
        st.markdown(
            "- Smoothing filters\n"
            "- Edge detection\n"
            "- Morphological operations\n"
            "- Object detection (contours)\n"
            "- Image transformation\n"
            "- Thresholding\n"
            "- Histogram modelling"
        )
    return mode, show_steps


def collect_inputs() -> list[tuple[str, bytes]]:
    """Return (name, image bytes) pairs from whichever input tab is used."""
    ui.panel_title("Add your document", "Upload photos, use your camera, or try a sample.")
    upload_tab, camera_tab, sample_tab = st.tabs(["Upload", "Camera", "Samples"])

    with upload_tab:
        files = st.file_uploader(
            "Upload one or more photos of documents",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            accept_multiple_files=True,
        )
    with camera_tab:
        # Only request camera permission once the user asks for it.
        use_camera = st.toggle("Turn on camera")
        photo = st.camera_input("Take a photo of a document") if use_camera else None
    with sample_tab:
        samples = sorted(SAMPLES_DIR.glob("*")) if SAMPLES_DIR.exists() else []
        chosen = st.multiselect(
            "Pick one or more sample photos", samples,
            format_func=lambda p: p.stem.replace("_", " ").title(),
        )

    inputs = [(f.name, f.getvalue()) for f in files or []]
    if photo is not None:
        inputs.append(("camera.jpg", photo.getvalue()))
    inputs += [(p.name, p.read_bytes()) for p in chosen]
    return inputs


def show_steps_grid(result: ScanResult) -> None:
    with st.expander("How this page was processed", expanded=False):
        columns = st.columns(4)
        for i, (key, image) in enumerate(result.steps.items()):
            title, detail = STEP_INFO[key]
            with columns[i % 4]:
                st.image(to_rgb(image), width="stretch")
                ui.step_caption(i + 1, title, detail)


def show_page(index: int, name: str, result: ScanResult, show_steps: bool):
    """Render one scanned page as a card and return the final (rotated) scan."""
    with st.container(border=True):
        ui.page_header(index + 1, name, result.document_found)
        rotate_col, download_col = st.columns(2, vertical_alignment="bottom")
        degrees = rotate_col.selectbox(
            "Rotate", [0, 90, 180, 270], key=f"rotate_{index}_{name}",
            format_func=lambda d: f"{d}°", label_visibility="collapsed",
        )
        scanned = rotate(result.scanned, degrees)
        download_col.download_button(
            "PNG", encode_png(scanned), icon=":material/download:",
            file_name=f"{Path(name).stem}_scanned.png", mime="image/png",
            key=f"png_{index}_{name}", width="stretch",
        )

        if not result.document_found:
            st.caption("No page outline was found, so the whole photo was used. "
                       "For best results, use a darker background and keep all four corners in view.")

        before, after = st.columns(2, gap="medium")
        with before:
            ui.label("Detected outline")
            st.image(to_rgb(result.steps["5_detected"]), width="stretch")
        with after:
            ui.label("Scanned result")
            st.image(to_rgb(scanned), width="stretch")

        if show_steps:
            show_steps_grid(result)
    return scanned


def main():
    st.set_page_config(page_title="Document Scanner", page_icon=":material/document_scanner:",
                       layout="wide")
    ui.inject_styles()
    mode, show_steps = sidebar()

    hero_col, input_col = st.columns([1.15, 1], gap="large")
    with hero_col:
        ui.hero()
    with input_col:
        inputs = collect_inputs()

    if not inputs:
        ui.empty_state()
        ui.footer()
        return

    with st.spinner("Scanning…"):
        scanned_inputs = []
        for name, data in inputs:
            try:
                scanned_inputs.append((name, *scan_bytes(data, mode)))
            except ValueError:
                st.error(f"Could not read {name}, so it was skipped.")
    if not scanned_inputs:
        return

    summary = st.container()

    # Two pages per row so wide screens are filled; a single page uses the full width.
    per_row = 1 if len(scanned_inputs) == 1 else 2
    scans = []
    for row_start in range(0, len(scanned_inputs), per_row):
        columns = st.columns(per_row, gap="medium")
        for column, (i, (name, result, _)) in zip(
            columns, enumerate(scanned_inputs[row_start:row_start + per_row], start=row_start)
        ):
            with column:
                scans.append(show_page(i, name, result, show_steps))

    # Filled after the pages so the PDF includes each page's chosen rotation.
    with summary:
        detected = sum(result.document_found for _, result, _ in scanned_inputs)
        total_time = sum(seconds for *_, seconds in scanned_inputs)
        pages_col, found_col, time_col, pdf_col = st.columns(4, vertical_alignment="center")
        pages_col.metric("Pages", len(scans))
        found_col.metric("Pages detected", f"{detected}/{len(scans)}")
        time_col.metric("Processing time", f"{total_time:.2f}s")
        pdf_col.download_button(
            "Download PDF", images_to_pdf(scans), icon=":material/picture_as_pdf:",
            file_name="scanned_document.pdf", mime="application/pdf",
            type="primary", width="stretch",
        )

    ui.footer()


if __name__ == "__main__":
    main()
