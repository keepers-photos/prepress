# pyright: reportMissingModuleSource=false

import os
import logging
import tempfile
import io
from PIL import Image, ImageDraw, ImageFont, ImageCms
from utils import calculate_spine_width_in_inches, image_to_pdf, process_image


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
    spine_width = INCH_TO_PX(calculate_spine_width_in_inches(page_count, is_hardcover))

    front_cover_path = process_image(front_cover_path, cover_width, cover_height)
    logging.debug(f"Front cover processed: {front_cover_path}")
    logging.debug(
        f"Front cover processed: {front_cover_path} ({cover_width}x{cover_height})"
    )
    front_cover = Image.open(front_cover_path)
    logging.debug(f"Front cover opened: {front_cover_path} {front_cover.size}")
    if verbose_mode:
        front_cover.save(f"{output_path}_debug_0_front_cover.jpg", dpi=(300, 300))

    # Paste the front cover
    total_width = (cover_width * 2) + spine_width + (wrap_margin * 2)
    total_height = cover_height + (wrap_margin * 2)
    full_cover = Image.new("CMYK", (total_width, total_height), color=(0, 0, 0, 0))
    front_cover_x = wrap_margin + cover_width + spine_width
    front_cover_y = wrap_margin
    full_cover.paste(front_cover, (front_cover_x, front_cover_y))
    logging.debug(f"Front cover pasted at ({front_cover_x}, {front_cover_y})")
    if verbose_mode:
        full_cover.save(f"{output_path}_debug_1_front_cover.jpg", dpi=(300, 300))

    # Add logo to the back cover
    logo_path = os.path.join(os.path.dirname(__file__), "resources", "logo.jpg")
    with Image.open(logo_path) as logo:
        logo_size = INCH_TO_PX(2 / 3)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        logo_x = wrap_margin + (cover_width - logo_size) // 2
        logo_y = total_height - wrap_margin - bleed_margin - logo_size - INCH_TO_PX(1)
        full_cover.paste(logo, (logo_x, logo_y))
        logging.debug(f"Logo pasted at ({logo_x}, {logo_y})")
    if verbose_mode:
        full_cover.save(f"{output_path}_debug_2_with_logo.jpg", dpi=(300, 300))

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
            (text_x, text_y), book_title, font=font, fill=(0, 0, 0, 89), anchor="mm"
        )
        logging.debug(f"Spine text added: {book_title} at ({text_x}, {text_y})")
        if verbose_mode:
            full_cover.save(
                f"{output_path}_debug_3_with_spine_text.jpg", dpi=(300, 300)
            )

    # Save as temporary PNG file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        full_cover.save(temp_file, "JPEG", resolution=DPI)
        temp_file_path = temp_file.name

    # Convert PNG to PDF using img2pdf
    image_to_pdf([temp_file_path], output_path)
    logging.info(f"Cover PDF generated: {output_path}")

    # Remove temporary file
    if not verbose_mode:
        os.unlink(temp_file_path)
