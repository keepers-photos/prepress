"""
.venv/bin/python prepress.py  \
    "LOUIE JACK SKERLJ DANIELSON 27 September 2003" \
    ./.data \
    ./ \
    28912-0 \
    --process cover \
    --cover_type soft_cover \
    --book_size square \
    --verbose
"""

# pyright: reportMissingModuleSource=false

import os
import logging

from cover import generate_cover_pdf
from interior import generate_interior_pdf

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process book pages and generate PDF")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )
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
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose mode to save intermediate images",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = "DEBUG" if args.verbose else args.log_level
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logging.info(f"Processing book: {args.book_title}")
    logging.info(f"Order ID: {args.order_id}")
    logging.info(f"Cover type: {args.cover_type}")
    logging.info(f"Book size: {args.book_size}")
    logging.info(f"Verbose mode: {'Enabled' if args.verbose else 'Disabled'}")
    logging.info(f"Log level: {log_level}")

    page_count = len(
        [f for f in os.listdir(args.input_path) if f.endswith(".png") and f != "0.png"]
    )
    logging.info(f"Number of pages: {page_count}")

    if args.process in ["pages", "all"]:
        interior_output_path = os.path.join(
            args.output_path,
            f"{args.order_id}-interior-{args.cover_type}-{args.book_size}.pdf",
        )
        generate_interior_pdf(
            args.input_path, interior_output_path, args.book_size, args.verbose
        )
        logging.info(f"Internal pages PDF generated: {interior_output_path}")

        # Check if the file was actually created in the output directory
        if not os.path.exists(interior_output_path):
            # If not, check if it was created in the input directory
            input_interior_path = os.path.join(
                args.input_path,
                f"{args.order_id}-interior-{args.cover_type}-{args.book_size}.pdf",
            )
            if os.path.exists(input_interior_path):
                # Move the file to the correct output directory
                os.rename(input_interior_path, interior_output_path)
                logging.info(
                    f"Moved interior PDF from input to output directory: {interior_output_path}"
                )
            else:
                logging.error(
                    "Internal PDF not found in either input or output directory."
                )

    if args.process in ["cover", "all"]:
        cover_output_path = os.path.join(
            args.output_path,
            f"{args.order_id}-cover-{args.cover_type}-{args.book_size}.pdf",
        )
        front_cover_path = os.path.join(args.input_path, "0.png")
        if os.path.exists(front_cover_path):
            generate_cover_pdf(
                front_cover_path,
                cover_output_path,
                page_count,
                args.book_size,
                args.cover_type == "hard_cover",
                args.book_title,
                args.verbose,
            )
            logging.info(f"Cover PDF generated: {cover_output_path}")
        else:
            logging.warning(
                "Front cover image (0.png) not found. Skipping cover generation."
            )

    logging.info("Processing complete.")
