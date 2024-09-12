import logging
import tempfile
import os
import io
from PIL import Image, ImageCms


cmyk_profile_path = os.path.join(
    os.path.dirname(__file__), "resources", "GRACoL2006_Coated1v2.icc"
)
cmyk_profile = ImageCms.getOpenProfile(cmyk_profile_path)
adobe_rgb_profile = ImageCms.getOpenProfile(
    os.path.join(os.path.dirname(__file__), "resources", "AdobeRGB1998.icc")
)


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
    try:
        with Image.open(input_file) as img:
            # Resize the image
            img = img.resize((width, height), Image.LANCZOS)
            img.info["dpi"] = (300, 300)

            # Convert from AdobeRGB to CMYK
            assert img.mode == "RGB"
            img = ImageCms.profileToProfile(
                img,
                inputProfile=adobe_rgb_profile,
                outputProfile=cmyk_profile,
                outputMode="CMYK",
            )

            # Save as temporary JPEG file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                img.save(
                    temp_file.name,
                    "JPEG",
                    quality=100,
                    subsampling=0,  # This ensures no chroma subsampling
                    icc_profile=cmyk_profile.tobytes(),
                    dpi=(300, 300),
                )
                return temp_file.name
    except Exception as e:
        logging.error(f"Error processing {input_file}: {str(e)}")
        return None


def image_to_pdf(image_files, output_path):
    # We use img2pdf to convert images to PDF because it's a simple, fast container
    # for images that retains the original image quality and color profiles.
    try:
        # Convert images to PDF using `img2pdf {image_files} -o {output_path}` on the command line
        sys_command = f"img2pdf {' '.join(image_files)} -o {output_path}"
        logging.debug(f"image_to_pdf - Running command: {sys_command}")
        os.system(sys_command)
    except Exception as e:
        logging.error(f"Error occurred while creating PDF: {e}")


def calculate_spine_width_in_inches(page_count, is_hardcover=False):
    if is_hardcover:
        # Hardcover spine width calculation
        if page_count <= 24:
            return 0.25 
        elif page_count <= 84:
            return 0.25 
        elif page_count <= 140:
            return 0.5 
        elif page_count <= 168:
            return 0.625 
        elif page_count <= 194:
            return 0.688 
        elif page_count <= 222:
            return 0.75 
        elif page_count <= 250:
            return 0.813 
        elif page_count <= 278:
            return 0.875 
        elif page_count <= 306:
            return 0.938 
        elif page_count <= 334:
            return 1.0 
        elif page_count <= 360:
            return 1.063 
        elif page_count <= 388:
            return 1.125 
        elif page_count <= 416:
            return 1.188 
        elif page_count <= 444:
            return 1.25 
        elif page_count <= 472:
            return 1.313 
        elif page_count <= 500:
            return 1.375 
        elif page_count <= 528:
            return 1.438 
        elif page_count <= 556:
            return 1.5 
        elif page_count <= 582:
            return 1.563 
        elif page_count <= 610:
            return 1.625 
        elif page_count <= 638:
            return 1.688 
        elif page_count <= 666:
            return 1.75 
        elif page_count <= 694:
            return 1.813 
        elif page_count <= 722:
            return 1.875 
        elif page_count <= 750:
            return 1.938 
        elif page_count <= 778:
            return 2.0 
        elif page_count <= 800:
            return 2.063 
        else:
            return 2.125 
    else:
        # Paperback spine width calculation
        return (page_count / 444 + 0.06) 
