"""Streamlit web frontend.

Run locally with:
    streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from scanner import DocumentScanner
from scanner.enhance import ScanMode
from scanner.utils import decode_image, encode_png, images_to_pdf, rotate, to_rgb

SAMPLES_DIR = Path(__file__).parent / "samples" / "internet"

MODE_LABELS = {
    ScanMode.BW: "Black & White",
    ScanMode.GRAY: "Grayscale",
    ScanMode.COLOR: "Magic Colour",
    ScanMode.ORIGINAL: "Original",
}

STEP_INFO = {
    "1_original": ("Original", "Input photo, resized for fast processing"),
    "2_grayscale": ("Grayscale", "Colour → single intensity channel"),
    "3_blurred": ("Gaussian Blur", "Smoothing filter removes noise"),
    "4_edges": ("Canny Edges", "Edge detection + morphological closing"),
    "5_detected": ("Page Detected", "Largest 4-corner contour"),
    "6_warped": ("Perspective Warp", "Top-down view of the page"),
    "7_scanned": ("Final Scan", "Thresholding / histogram equalization"),
}


@st.cache_data(show_spinner=False, max_entries=32)
def scan_bytes(data: bytes, mode: ScanMode):
    return DocumentScanner(mode=mode).scan(decode_image(data))


def collect_inputs() -> list[tuple[str, bytes]]:
    """Return (name, image bytes) pairs from whichever input tab is used."""
    upload_tab, camera_tab, sample_tab = st.tabs(["📁 Upload", "📷 Camera", "🖼️ Try a sample"])

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
        chosen = st.multiselect("Pick sample photos", samples, format_func=lambda p: p.stem)

    inputs = [(f.name, f.getvalue()) for f in files or []]
    if photo is not None:
        inputs.append(("camera.jpg", photo.getvalue()))
    inputs += [(p.name, p.read_bytes()) for p in chosen]
    return inputs


def show_page(index: int, name: str, data: bytes, mode: ScanMode, show_steps: bool):
    """Render one scanned page and return the final (rotated) scan."""
    result = scan_bytes(data, mode)

    header, rotate_col = st.columns([3, 1])
    header.subheader(f"Page {index + 1} · {name}")
    degrees = rotate_col.selectbox(
        "Rotate", [0, 90, 180, 270], key=f"rotate_{index}_{name}",
        format_func=lambda d: f"{d}°",
    )
    scanned = rotate(result.scanned, degrees)

    if result.document_found:
        st.success("Document outline detected", icon="✅")
    else:
        st.warning("No page outline found, so the whole image was used. "
                   "Try a darker background with all four corners visible.", icon="⚠️")

    before, after = st.columns(2)
    before.image(to_rgb(result.steps["5_detected"]), caption="Detected outline",
                 width="stretch")
    after.image(to_rgb(scanned), caption="Scanned result", width="stretch")

    st.download_button(
        "⬇️ Download PNG", encode_png(scanned),
        file_name=f"{Path(name).stem}_scanned.png", mime="image/png",
        key=f"png_{index}_{name}",
    )

    if show_steps:
        with st.expander("🔍 Processing steps", expanded=True):
            columns = st.columns(4)
            for i, (key, image) in enumerate(result.steps.items()):
                title, detail = STEP_INFO[key]
                with columns[i % 4]:
                    st.image(to_rgb(image), width="stretch")
                    st.markdown(f"**{i + 1}. {title}**  \n{detail}")

    st.divider()
    return scanned


def main():
    st.set_page_config(page_title="Document Scanner", page_icon="📄", layout="wide")

    with st.sidebar:
        st.header("⚙️ Settings")
        mode = st.radio("Scan mode", list(ScanMode), format_func=MODE_LABELS.get)
        show_steps = st.toggle("Show processing steps", value=True)
        st.divider()
        st.markdown(
            "**How it works**\n\n"
            "1. Grayscale + Gaussian blur\n"
            "2. Canny edge detection\n"
            "3. Morphological closing\n"
            "4. Contour detection (4 corners)\n"
            "5. Perspective transform\n"
            "6. Adaptive threshold / CLAHE"
        )

    st.title("📄 Document Scanner")
    st.caption("Turn a photo of a page into a clean, flat scan. Built with OpenCV and NumPy.")

    inputs = collect_inputs()
    if not inputs:
        st.info("Upload a photo, use your camera, or pick a sample to get started.")
        return

    scans = []
    with st.spinner("Scanning…"):
        for i, (name, data) in enumerate(inputs):
            try:
                scans.append(show_page(i, name, data, mode, show_steps))
            except ValueError:
                st.error(f"Could not read {name}, so it was skipped.")

    if scans:
        st.download_button(
            f"📑 Download all {len(scans)} page(s) as PDF", images_to_pdf(scans),
            file_name="scanned_document.pdf", mime="application/pdf", type="primary",
        )


if __name__ == "__main__":
    main()
