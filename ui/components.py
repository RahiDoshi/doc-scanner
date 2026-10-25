"""Small HTML building blocks styled by styles.css."""

from html import escape
from pathlib import Path

import streamlit as st

STYLES_PATH = Path(__file__).parent / "styles.css"

PIPELINE = ["Grayscale", "Gaussian blur", "Canny edges", "Contours", "Perspective warp", "Enhance"]

FEATURES = [
    ("Auto page detection", "Finds the page outline even when it's tilted or photographed at an angle."),
    ("Perspective correction", "Flattens the page into a straight, top-down view."),
    ("Four scan styles", "Black & white, grayscale, magic colour, or the original colours."),
    ("PDF export", "Scan several pages and download them together as one PDF."),
]


def inject_styles() -> None:
    st.html(f"<style>{STYLES_PATH.read_text(encoding='utf-8')}</style>")


def hero() -> None:
    chips = "".join(f'<span class="chip">{t}</span>' for t in ["OpenCV", "NumPy", "Python", "Streamlit"])
    st.html(
        '<div class="hero"><div>'
        '<div class="eyebrow">IPCV Mini Project</div>'
        "<h1>Document<br>Scanner.</h1>"
        "<p>Turn a photo of a page into a clean, flat, high-contrast scan. "
        "Works like CamScanner and is built from classic image processing, with no machine learning.</p>"
        f"</div><div>{chips}</div></div>"
    )


def panel_title(title: str, subtitle: str) -> None:
    st.html(f'<div class="panel-title">{escape(title)}</div><div class="panel-sub">{escape(subtitle)}</div>')


def empty_state() -> None:
    cards = "".join(
        f'<div class="feature"><div class="num">0{i}</div><h4>{title}</h4><p>{text}</p></div>'
        for i, (title, text) in enumerate(FEATURES, start=1)
    )
    stages = '<span class="arrow">→</span>'.join(f'<span class="stage">{s}</span>' for s in PIPELINE)
    st.html(
        f'<div class="feature-grid">{cards}</div>'
        '<div class="pipeline-wrap"><div class="section-title">How it works</div>'
        f'<div class="pipeline">{stages}</div></div>'
    )


def page_header(number: int, name: str, found: bool) -> None:
    badge = (
        '<span class="badge ok">Page detected</span>' if found
        else '<span class="badge warn">Full image used</span>'
    )
    st.html(
        f'<div class="page-head"><span class="page-num">{number}</span>'
        f'<span class="page-name">{escape(name)}</span>{badge}</div>'
    )


def label(text: str) -> None:
    st.html(f'<div class="img-label">{escape(text)}</div>')


def step_caption(number: int, title: str, detail: str) -> None:
    st.html(
        f'<div class="step-title"><span>{number}</span>{escape(title)}</div>'
        f'<div class="step-detail">{escape(detail)}</div>'
    )


def footer() -> None:
    st.html('<div class="footer">IPCV MINI PROJECT · DOCUMENT SCANNER</div>')
