# pyright: reportMissingModuleSource=false

import os
import logging
from multiprocessing import Pool, cpu_count

from utils import print_progress, process_image, create_pdf


def generate_interior_pdf(input_path, output_path, book_size, debug=False):
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    png_files = sorted(
        [f for f in os.listdir(input_path) if f.endswith(".png") and f != "0.png"],
        key=lambda x: int(os.path.splitext(x)[0]),
    )

    if not png_files:
        logging.warning(f"No matching PNG files found in {input_path}")
        return

    if book_size == "square":
        page_size = 2625  # 8.75 inches at 300 DPI
    elif book_size == "small_square":
        page_size = 2325  # 7.75 inches at 300 DPI
    else:
        raise ValueError(f"Unsupported book size: {book_size}")

    logging.info("Processing images:")
    total = len(png_files)
    processed_files = []
    with Pool(processes=cpu_count()) as pool:
        args = [
            (
                os.path.join(input_path, f),
                page_size,
                page_size,
            )
            for f in png_files
        ]
        for i, result in enumerate(pool.starmap(process_image, args), 1):
            processed_files.append(result)
            print_progress(i, total, prefix="Progress:", suffix="Complete", length=50)

    processed_files = [f for f in processed_files if f is not None]

    if not processed_files:
        logging.warning("No images were successfully processed")
        return

    logging.info("Combining images into PDF...")
    create_pdf(processed_files, output_path)

    if not debug:
        logging.info("Cleaning up temporary files...")
        for file in processed_files:
            os.remove(file)
    else:
        logging.info("Debug mode: Keeping temporary files...")
