# pyright: reportMissingModuleSource=false

import os
import sys
import glob
import subprocess
import logging
from multiprocessing import Pool, cpu_count

from PIL import Image, ImageDraw
from reportlab.lib.units import inch

from cover import generate_cover_pdf
from utils import print_progress

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_image(args):
    input_file, output_file, is_right_page, book_size = args
    if book_size == "square":
        page_width = page_height = 2625  # 8.75 inches at 300 DPI
    elif book_size == "small_square":
        page_width = page_height = 2325  # 7.75 inches at 300 DPI
    else:
        raise ValueError(f"Unsupported book size: {book_size}")

    command = [
        "convert",
        input_file,
        "-density",
        "300",
        "-units",
        "PixelsPerInch",
        "-resize",
        f"{page_width}x{page_height}",
        "-background",
        "white",
        "-quality",
        "100",
        "-compress",
        "None",
        output_file,
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logging.debug(f"Successfully processed {input_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {input_file}:")
        logging.error(f"Command: {' '.join(command)}")
        logging.error(f"Return code: {e.returncode}")
        logging.error(f"stdout: {e.stdout}")
        logging.error(f"stderr: {e.stderr}")
        return None


def process_images(input_path, output_path, book_size):
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    png_files = sorted(
        [f for f in os.listdir(input_path) if f.endswith(".png") and f != "0.png"],
        key=lambda x: int(os.path.splitext(x)[0]),
    )

    if not png_files:
        logging.warning(f"No matching PNG files found in {input_path}")
        return

    temp_dir = os.path.join(os.path.dirname(output_path), "temp_processed")
    os.makedirs(temp_dir, exist_ok=True)

    args = [
        (
            os.path.join(input_path, f),
            os.path.join(temp_dir, f"{i}.png"),
            i % 2 == 1,
            book_size,
        )
        for i, f in enumerate(png_files, start=1)
    ]

    logging.info("Processing images:")
    total = len(args)
    processed_files = []
    with Pool(processes=cpu_count()) as pool:
        for i, result in enumerate(pool.imap(process_image, args), 1):
            processed_files.append(result)
            print_progress(i, total, prefix="Progress:", suffix="Complete", length=50)

    processed_files = [f for f in processed_files if f is not None]

    if not processed_files:
        logging.warning("No images were successfully processed")
        return

    logging.info("Combining images into PDF...")
    combine_command = ["convert", *processed_files, output_path]

    try:
        subprocess.run(
            combine_command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logging.info(f"PDF created successfully at {output_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error occurred while creating PDF: {e}")

    logging.info("Cleaning up temporary files...")
    for file in processed_files:
        os.remove(file)
    os.rmdir(temp_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process book pages and generate PDF")
    parser.add_argument("book_title", help="Title of the book")
    parser.add_argument("input_path", help="Input directory containing image files")
    parser.add_argument("output_path", help="Output directory for generated PDFs")
    parser.add_argument("order_id", help="Order ID (e.g., 28912-0)")
    parser.add_argument(
        "--process",
        choices=["cover", "pages", "all"],
        default="all",
        help="Specify what to process: cover, pages, or all (default: all)",
    )
    parser.add_argument(
        "--cover_type",
        choices=["soft_cover", "hard_cover"],
        default="hard_cover",
        help="Specify the cover type: soft_cover or hard_cover (default: hard_cover)",
    )
    parser.add_argument(
        "--book_size",
        choices=["square", "small_square"],
        default="square",
        help="Specify the book size: square (8.75x8.75 inches) or small_square (7x7 inches)",
    )

    args = parser.parse_args()

    logging.info(f"Processing book: {args.book_title}")
    logging.info(f"Order ID: {args.order_id}")
    logging.info(f"Cover type: {args.cover_type}")
    logging.info(f"Book size: {args.book_size}")

    page_count = len(
        [f for f in os.listdir(args.input_path) if f.endswith(".png") and f != "0.png"]
    )
    logging.info(f"Number of pages: {page_count}")

    if args.process in ["pages", "all"]:
        internal_output_path = os.path.join(
            args.output_path, f"{args.order_id}-internal.pdf"
        )
        process_images(args.input_path, internal_output_path, args.book_size)
        logging.info(f"Internal pages PDF generated: {internal_output_path}")

        # Check if the file was actually created in the output directory
        if not os.path.exists(internal_output_path):
            # If not, check if it was created in the input directory
            input_internal_path = os.path.join(
                args.input_path, f"{args.order_id}-internal.pdf"
            )
            if os.path.exists(input_internal_path):
                # Move the file to the correct output directory
                os.rename(input_internal_path, internal_output_path)
                logging.info(
                    f"Moved internal PDF from input to output directory: {internal_output_path}"
                )
            else:
                logging.error(
                    "Internal PDF not found in either input or output directory."
                )

    if args.process in ["cover", "all"]:
        cover_output_path = os.path.join(args.output_path, f"{args.order_id}-cover.pdf")
        front_cover_path = os.path.join(args.input_path, "0.png")
        if os.path.exists(front_cover_path):
            generate_cover_pdf(
                front_cover_path,
                cover_output_path,
                page_count,
                args.cover_type == "hard_cover",
                args.book_title,
            )
            logging.info(f"Cover PDF generated: {cover_output_path}")
        else:
            logging.warning(
                "Front cover image (0.png) not found. Skipping cover generation."
            )

    logging.info("Processing complete.")
