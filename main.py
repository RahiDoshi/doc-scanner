"""Command-line entry point.

Examples:
    python main.py samples/page.jpg
    python main.py samples/page.jpg --mode color --steps --show
"""

import argparse
from pathlib import Path

import cv2

from scanner import DocumentScanner
from scanner.enhance import ScanMode
from scanner.utils import (
    images_to_pdf, load_image, make_step_grid, rotate, save_image, save_steps,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan a document from a photo.")
    parser.add_argument("input", type=Path, help="path to the input photo")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("output"))
    parser.add_argument(
        "-m", "--mode", type=ScanMode, choices=list(ScanMode), default=ScanMode.BW,
        help="output style (default: bw)",
    )
    parser.add_argument(
        "-r", "--rotate", type=int, choices=[0, 90, 180, 270], default=0,
        help="rotate the scan clockwise by this many degrees",
    )
    parser.add_argument("--pdf", action="store_true", help="also save the scan as a PDF")
    parser.add_argument("--steps", action="store_true", help="save every intermediate step")
    parser.add_argument("--show", action="store_true", help="display the step-by-step result")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image = load_image(args.input)

    result = DocumentScanner(mode=args.mode).scan(image)
    if not result.document_found:
        print("Warning: no document outline found, using the full image.")

    scanned = rotate(result.scanned, args.rotate)
    out_path = args.output_dir / f"{args.input.stem}_scanned.png"
    save_image(out_path, scanned)
    print(f"Saved scan to {out_path}")

    if args.pdf:
        pdf_path = out_path.with_suffix(".pdf")
        pdf_path.write_bytes(images_to_pdf([scanned]))
        print(f"Saved PDF to {pdf_path}")

    if args.steps:
        steps_dir = args.output_dir / f"{args.input.stem}_steps"
        save_steps(result.steps, steps_dir)
        save_image(steps_dir / "all_steps.png", make_step_grid(result.steps))
        print(f"Saved intermediate steps to {steps_dir}")

    if args.show:
        cv2.imshow("Document Scanner - steps", make_step_grid(result.steps, tile_height=250))
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
