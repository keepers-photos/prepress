import logging
import subprocess
import tempfile
import os
import img2pdf

def print_progress(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=50,
    fill="█",
    print_end="\r",
):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    logging.info(f"\r{prefix} |{bar}| {percent}% {suffix}")

def process_image(input_file, width, height):
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        temp_output = temp_file.name

    command = [
        "convert",
        input_file,
        "-colorspace",
        "sRGB",
        "-density",
        "300",
        "-units",
        "PixelsPerInch",
        "-resize",
        f"{width}x{height}!",  # Force resize to exact dimensions
        "-quality",
        "100",
        "-compress",
        "None",
        temp_output,
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logging.debug(f"Successfully processed {input_file}")
        return temp_output
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {input_file}:")
        logging.error(f"Command: {' '.join(command)}")
        logging.error(f"Return code: {e.returncode}")
        logging.error(f"stdout: {e.stdout}")
        logging.error(f"stderr: {e.stderr}")
        os.unlink(temp_output)
        return None

def create_pdf(image_files, output_path, dpi=300):
    try:
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_files, dpi=dpi))
        logging.info(f"PDF created successfully at {output_path}")
    except Exception as e:
        logging.error(f"Error occurred while creating PDF: {e}")
