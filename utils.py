import logging
import subprocess


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

def process_image(input_file, output_file, width, height):
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
