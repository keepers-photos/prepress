import os
import sys
import glob
import subprocess
import logging
from multiprocessing import Pool, cpu_count

from PIL import Image, ImageDraw
from utils import print_progress
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# pyright: reportMissingModuleSource=false


def calculate_spine_width(page_count, is_hardcover=False):
    if is_hardcover:
        # Hardcover spine width calculation
        if page_count <= 24:
            return 0.25 * inch
        elif page_count <= 84:
            return 0.25 * inch
        elif page_count <= 140:
            return 0.5 * inch
        elif page_count <= 168:
            return 0.625 * inch
        elif page_count <= 194:
            return 0.688 * inch
        elif page_count <= 222:
            return 0.75 * inch
        elif page_count <= 250:
            return 0.813 * inch
        elif page_count <= 278:
            return 0.875 * inch
        elif page_count <= 306:
            return 0.938 * inch
        elif page_count <= 334:
            return 1.0 * inch
        elif page_count <= 360:
            return 1.063 * inch
        elif page_count <= 388:
            return 1.125 * inch
        elif page_count <= 416:
            return 1.188 * inch
        elif page_count <= 444:
            return 1.25 * inch
        elif page_count <= 472:
            return 1.313 * inch
        elif page_count <= 500:
            return 1.375 * inch
        elif page_count <= 528:
            return 1.438 * inch
        elif page_count <= 556:
            return 1.5 * inch
        elif page_count <= 582:
            return 1.563 * inch
        elif page_count <= 610:
            return 1.625 * inch
        elif page_count <= 638:
            return 1.688 * inch
        elif page_count <= 666:
            return 1.75 * inch
        elif page_count <= 694:
            return 1.813 * inch
        elif page_count <= 722:
            return 1.875 * inch
        elif page_count <= 750:
            return 1.938 * inch
        elif page_count <= 778:
            return 2.0 * inch
        elif page_count <= 800:
            return 2.063 * inch
        else:
            return 2.125 * inch
    else:
        # Paperback spine width calculation
        return (page_count / 444 + 0.06) * inch


def generate_cover_pdf(
    front_cover_path, output_path, page_count, is_hardcover=False, book_title=""
):
    # Define bleed margin
    bleed_margin = 0.125 * inch
    cover_width = 8.5 * inch + 2 * bleed_margin
    cover_height = 8.5 * inch + 2 * bleed_margin

    # Define wrap margins (only for hardcover)
    wrap_margin = 0.75 * inch if is_hardcover else 0

    # Calculate dimensions
    spine_width = calculate_spine_width(page_count, is_hardcover)
    total_width = (cover_width * 2) + spine_width + (wrap_margin * 2)
    total_height = cover_height + (wrap_margin * 2)

    # Load and resize the front cover image
    front_cover = Image.open(front_cover_path)
    front_cover.thumbnail((int(cover_width), int(cover_height)), Image.LANCZOS)

    # Create a new image with the correct size and paste the resized cover
    new_front_cover = Image.new(
        "RGB", (int(cover_width), int(cover_height)), (255, 255, 255)
    )
    paste_x = (int(cover_width) - front_cover.width) // 2
    paste_y = (int(cover_height) - front_cover.height) // 2
    new_front_cover.paste(front_cover, (paste_x, paste_y))
    front_cover = new_front_cover

    # Log the size including wrap, bleed, and spine width
    logging.info(
        f"Cover size (with wrap and bleed): {total_width / inch:.2f} x {total_height / inch:.2f} inch"
    )
    logging.info(f"({total_width:.2f}mm x {total_height:.2f}mm)")
    logging.info(f"Spine width: {spine_width / inch:.3f} inch ({spine_width:.2f}mm)")

    # Create a new image for the full cover (front, spine, back, with margins and bleed)
    full_cover = Image.new("RGB", (int(total_width), int(total_height)), color="white")

    # Paste the front cover
    front_cover_position = (
        int(wrap_margin + cover_width + spine_width),
        int(wrap_margin + bleed_margin),
    )
    full_cover.paste(front_cover, front_cover_position)

    # Load and paste the logo on the back cover
    logo = Image.open("logo.jpg")
    logo_size = int(
        2 * inch / 3
    )  # Set logo size to 2/3 inch (1/3 of original 2 inches)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    # Calculate logo position (centered horizontally, 1 inch from bottom)
    logo_x = int(wrap_margin + (cover_width - logo_size) / 2)
    logo_y = int(total_height - wrap_margin - bleed_margin - logo_size - inch)

    full_cover.paste(logo, (logo_x, logo_y))

    # Create the PDF
    c = canvas.Canvas(output_path, pagesize=(total_width, total_height))

    # Draw the full cover image
    c.drawInlineImage(full_cover, 0, 0, total_width, total_height)

    # Add spine text here if the page_count is over 80
    if page_count > 80:
        # Register the font (assuming SF-Pro.ttf is in the same directory as the script)
        pdfmetrics.registerFont(TTFont("SF-Pro", "SF-Pro.ttf"))
        c.setFont("SF-Pro", 12)

        # Calculate the position for the spine text.
        # -bleed_margin is to account for the bleed margin on the right side of the spine
        spine_center_x = wrap_margin + cover_width - bleed_margin + (spine_width / 2)
        spine_center_y = total_height / 2

        # Save the current state
        c.saveState()

        # Translate to the spine center, rotate, and draw the text
        c.translate(spine_center_x, spine_center_y)
        c.rotate(-90)
        text_width = c.stringWidth(book_title, "SF-Pro", 12)
        c.drawString(-text_width / 2, 0, book_title)

        # Restore the previous state
        c.restoreState()

    c.showPage()
    c.save()


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
