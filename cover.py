# pyright: reportMissingModuleSource=false

import os
import logging
import tempfile
import io
from PIL import Image, ImageDraw, ImageFont, ImageCms
from utils import create_pdf

# Add the path to the Adobe RGB ICC profile
ADOBE_RGB_PROFILE_PATH = os.path.join(os.path.dirname(__file__), "resources", "AdobeRGB1998.icc")

# Define the inch constant
inch = 1


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
    front_cover_path,
    output_path,
    page_count,
    size_type="square",
    is_hardcover=False,
    book_title="",
    verbose_mode=False,
):
    """
    Generate a cover PDF using PIL/Pillow and img2pdf.

    This function performs the following steps:
    1. Load and process the front cover image
    2. Extend the image to the west to accommodate the back cover and spine
    3. Add wrap margin if needed (for hardcover)
    4. Add logo to the back cover
    5. Add spine text if the page count is over 80
    6. Convert the final image to PDF using img2pdf

    The function maintains a 300 DPI resolution throughout the process and
    converts the color profile from AdobeRGB to sRGB.

    If verbose_mode is True, intermediate images are saved for inspection.
    """

    # Define constants
    DPI = 300
    INCH_TO_PX = lambda inches: int(inches * DPI)

    # Define dimensions
    bleed_margin = INCH_TO_PX(0.125)
    cover_width = INCH_TO_PX(8.5 if size_type == "square" else 7.5) + bleed_margin
    cover_height = INCH_TO_PX(8.5 if size_type == "square" else 7.5) + 2 * bleed_margin
    wrap_margin = INCH_TO_PX(0.75) if is_hardcover else 0
    spine_width = INCH_TO_PX(calculate_spine_width(page_count, is_hardcover))

    total_width = (cover_width * 2) + spine_width + (wrap_margin * 2)
    total_height = cover_height + (wrap_margin * 2)

    # Load and process the front cover image
    with Image.open(front_cover_path) as img:
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
                    outputMode="RGB"
                )
                
                if verbose_mode:
                    logging.info("Color profile converted from Adobe RGB to sRGB")
            except Exception as e:
                logging.warning(f"Failed to convert color profile: {e}. Proceeding with original image.")

        # Resize the image
        img = img.resize((cover_width, cover_height), Image.LANCZOS)

        # Create a new image with white background
        front_cover = Image.new("RGB", (cover_width, cover_height), "white")
        # Paste the resized image onto the white background
        front_cover.paste(img, (0, 0), img if img.mode == "RGBA" else None)

    if verbose_mode:
        front_cover.save(f"{output_path}_debug_0_front_cover.png")

    # Create a new image for the full cover
    full_cover = Image.new("RGB", (total_width, total_height), color="white")

    # Paste the front cover
    front_cover_x = wrap_margin + cover_width + spine_width
    front_cover_y = wrap_margin
    full_cover.paste(front_cover, (front_cover_x, front_cover_y))
    if verbose_mode:
        full_cover.save(f"{output_path}_debug_1_front_cover.png")

    # Add logo to the back cover
    logo_path = os.path.join(os.path.dirname(__file__), "resources", "logo.jpg")
    with Image.open(logo_path) as logo:
        logo_size = INCH_TO_PX(2 / 3)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        logo_x = wrap_margin + (cover_width - logo_size) // 2
        logo_y = total_height - wrap_margin - bleed_margin - logo_size - INCH_TO_PX(1)
        full_cover.paste(logo, (logo_x, logo_y))
    if verbose_mode:
        full_cover.save(f"{output_path}_debug_2_with_logo.png")

    # Add spine text if page count is over 80
    if page_count > 80:
        draw = ImageDraw.Draw(full_cover)
        font_path = "SF-Pro.ttf"
        font_size = min(12, (spine_width - 2 * bleed_margin) // 4)
        font = ImageFont.truetype(font_path, font_size)

        spine_center_x = wrap_margin + cover_width + spine_width // 2
        spine_top_y = wrap_margin + bleed_margin + INCH_TO_PX(1)

        bbox = draw.textbbox((0, 0), book_title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = spine_center_x - text_height // 2
        text_y = spine_top_y + (cover_height - text_width) // 2

        draw.text(
            (text_x, text_y), book_title, font=font, fill=(89, 89, 89), anchor="mm"
        )
        if verbose_mode:
            full_cover.save(f"{output_path}_debug_3_with_spine_text.png")

    # Save as temporary PNG file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        full_cover.save(temp_file, "PNG", resolution=DPI)
        temp_file_path = temp_file.name

    # Convert PNG to PDF using img2pdf
    create_pdf([temp_file_path], output_path, dpi=DPI)

    # Remove temporary file
    if not verbose_mode:
        os.unlink(temp_file_path)
    logging.info(f"Cover PDF generated: {output_path}")
