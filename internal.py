# pyright: reportMissingModuleSource=false

import os
import subprocess
import logging
from multiprocessing import Pool, cpu_count

from utils import print_progress


def process_image(args):
    input_file, output_file, is_right_page, book_size = args
    if book_size == "square":
        page_size = 2625  # 8.75 inches at 300 DPI
    elif book_size == "small_square":
        page_size = 2325  # 7.75 inches at 300 DPI
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
        f"{page_size}x{page_size}!",  # Force resize to exact dimensions
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


def generate_internal_pdf(input_path, output_path, book_size):
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
