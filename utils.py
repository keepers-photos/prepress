import logging
import tempfile
import os
import io
import img2pdf
from PIL import Image, ImageCms
import pikepdf

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
            # Define the path to the CMYK ICC profile
            cmyk_profile_path = os.path.join(os.path.dirname(__file__), "resources", "GRACoL2006_Coated1v2.icc")
            
            # Convert color space if needed (assuming input is Adobe RGB)
            if img.mode == "RGB":
                try:
                    # Create CMYK profile
                    cmyk_profile = ImageCms.getOpenProfile(cmyk_profile_path)
                    
                    # Use the provided Adobe RGB profile
                    adobe_rgb_profile = ImageCms.getOpenProfile(os.path.join(os.path.dirname(__file__), "resources", "AdobeRGB1998.icc"))

                    # Convert directly to CMYK
                    img = ImageCms.profileToProfile(
                        img, 
                        inputProfile=adobe_rgb_profile, 
                        outputProfile=cmyk_profile, 
                        outputMode="CMYK"
                    )
                    
                    logging.debug(f"Color profile converted from Adobe RGB to CMYK for {input_file}")
                except ImageCms.PyCMSError as e:
                    logging.warning(f"Failed to convert color profile for {input_file}: {e}. Proceeding with original image.")
                except Exception as e:
                    logging.error(f"Unexpected error during color profile conversion for {input_file}: {e}. Proceeding with original image.")

            # Resize the image
            img = img.resize((width, height), Image.LANCZOS)

            # Save the processed image
            img.save(temp_output, "PNG", icc_profile=ImageCms.getOpenProfile(cmyk_profile_path).tobytes(), resolution=300, quality=100)

        logging.debug(f"Successfully processed {input_file}")
        return temp_output
    except Exception as e:
        logging.error(f"Error processing {input_file}: {str(e)}")
        os.unlink(temp_output)
        return None


def create_pdf(image_files, output_path, dpi=300):
    try:
        pdf_bytes = img2pdf.convert(image_files, dpi=dpi)
        
        # Create a temporary file for the initial PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        # Open the temporary PDF and embed the CMYK color profile
        with pikepdf.Pdf.open(temp_pdf_path) as pdf:
            cmyk_profile_path = os.path.join(os.path.dirname(__file__), "resources", "GRACoL2006_Coated1v2.icc")
            with open(cmyk_profile_path, 'rb') as icc:
                icc_profile = icc.read()
            
            pdf.add_attachment('GRACoL2006_Coated1v2.icc', icc_profile)
            
            for page in pdf.pages:
                page.add_resource(pikepdf.Name.ColorSpace, pikepdf.Name.DefaultCMYK, 
                                  pikepdf.Array([pikepdf.Name.ICCBased, pdf.make_indirect(pikepdf.Stream(pdf, icc_profile))]))

            pdf.save(output_path)

        # Remove the temporary PDF file
        os.unlink(temp_pdf_path)

        logging.info(f"PDF created successfully with embedded CMYK profile at {output_path}")
    except Exception as e:
        logging.error(f"Error occurred while creating PDF: {e}")
