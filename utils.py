import logging
import tempfile
import os
import io
import img2pdf
from PIL import Image, ImageCms
import pikepdf


cmyk_profile_path = os.path.join(os.path.dirname(__file__), "resources", "GRACoL2006_Coated1v2.icc")
cmyk_profile = ImageCms.getOpenProfile(cmyk_profile_path)
adobe_rgb_profile = ImageCms.getOpenProfile(os.path.join(os.path.dirname(__file__), "resources", "AdobeRGB1998.icc"))


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
            
            # Convert from AdobeRGB to CMYK
            if img.mode == "RGB":
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
                )
                return temp_file.name
    except Exception as e:
        logging.error(f"Error processing {input_file}: {str(e)}")
        return None


def images_to_pdf(image_files, output_path, dpi=300):
    try:
        pdf_bytes = img2pdf.convert(image_files, dpi=dpi)

        # Create a temporary file for the initial PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        # Open the temporary PDF and embed the CMYK color profile
        with pikepdf.Pdf.open(temp_pdf_path) as pdf:
            with open(cmyk_profile_path, "rb") as icc:
                icc_profile = icc.read()

            pdf.add_attachment("GRACoL2006_Coated1v2.icc", icc_profile)
            for page in pdf.pages:
                page.add_resource(
                    pikepdf.Name.ColorSpace,
                    pikepdf.Name.DefaultCMYK,
                    pikepdf.Array(
                        [
                            pikepdf.Name.ICCBased,
                            pdf.make_indirect(pikepdf.Stream(pdf, icc_profile)),
                        ]
                    ),
                )

            pdf.save(output_path)

        # Remove the temporary PDF file
        os.unlink(temp_pdf_path)

        logging.info(
            f"PDF created successfully with embedded CMYK profile at {output_path}"
        )
    except Exception as e:
        logging.error(f"Error occurred while creating PDF: {e}")


def calculate_spine_width_in_inches(page_count, is_hardcover=False):
    inch = 1
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
