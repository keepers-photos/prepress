import logging
import tempfile
import os
import io
import img2pdf
from PIL import Image, ImageCms

# Add the path to the Adobe RGB ICC profile
ADOBE_RGB_PROFILE_PATH = os.path.join(os.path.dirname(__file__), "resources", "AdobeRGB1998.icc")


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
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_output = temp_file.name

    try:
        with Image.open(input_file) as img:
            # Convert color space if needed (assuming input is Adobe RGB)
            if img.mode == "RGB":
                try:
                    # Create sRGB profile
                    srgb_profile = ImageCms.createProfile("sRGB")
                    
                    # Use the provided Adobe RGB profile
                    adobe_rgb_profile = ImageCms.getOpenProfile(ADOBE_RGB_PROFILE_PATH)

                    # Convert to sRGB
                    img = ImageCms.profileToProfile(
                        img, 
                        inputProfile=adobe_rgb_profile, 
                        outputProfile=srgb_profile, 
                        outputMode="RGB",
                        renderingIntent=ImageCms.INTENT_RELATIVE_COLORIMETRIC
                    )
                    
                    logging.debug(f"Color profile converted from Adobe RGB to sRGB for {input_file}")
                except Exception as e:
                    logging.warning(f"Failed to convert color profile for {input_file}: {e}. Proceeding with original image.")

            # Resize the image
            img = img.resize((width, height), Image.LANCZOS)

            # Save the processed image
            img.save(temp_output, "PNG", resolution=300, quality=100)

        logging.debug(f"Successfully processed {input_file}")
        return temp_output
    except Exception as e:
        logging.error(f"Error processing {input_file}: {str(e)}")
        os.unlink(temp_output)
        return None


def create_pdf(image_files, output_path, dpi=300):
    try:
        pdf_bytes = img2pdf.convert(image_files, dpi=dpi)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        logging.info(f"PDF created successfully at {output_path}")
    except Exception as e:
        logging.error(f"Error occurred while creating PDF: {e}")
