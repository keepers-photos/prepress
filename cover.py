import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

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
    front_cover_path, output_path, page_count, is_hardcover=False, book_title=""
):
    # Define bleed margin
    bleed_margin = 0.125 * inch
    cover_width = 8.5 * inch + bleed_margin
    cover_height = 8.5 * inch + 2 * bleed_margin

    # Define wrap margins (only for hardcover)
    wrap_margin = 0.75 * inch if is_hardcover else 0

    # Calculate dimensions
    spine_width = calculate_spine_width(page_count, is_hardcover)
    total_width = (cover_width * 2) + spine_width + (wrap_margin * 2)
    total_height = cover_height + (wrap_margin * 2)

    # Load and resize the front cover image
    front_cover = Image.open(front_cover_path)
    front_cover.thumbnail((int(cover_width), int(cover_height)), Image.LANCZOS)

    # Create a new image with the correct size and paste the resized cover
    new_front_cover = Image.new(
        "RGB", (int(cover_width), int(cover_height)), (255, 255, 255)
    )
    paste_x = (int(cover_width) - front_cover.width) // 2
    paste_y = (int(cover_height) - front_cover.height) // 2
    new_front_cover.paste(front_cover, (paste_x, paste_y))
    front_cover = new_front_cover

    # Log the size including wrap, bleed, and spine width
    logging.info(
        f"Cover size (with wrap and bleed): {total_width / inch:.2f} x {total_height / inch:.2f} inch"
    )
    logging.info(f"({total_width:.2f}mm x {total_height:.2f}mm)")
    logging.info(f"Spine width: {spine_width / inch:.3f} inch ({spine_width:.2f}mm)")

    # Create a new image for the full cover (front, spine, back, with margins and bleed)
    full_cover = Image.new("RGB", (int(total_width), int(total_height)), color="white")

    # Paste the front cover
    front_cover_position = (
        int(wrap_margin + cover_width + spine_width),
        int(wrap_margin + bleed_margin),
    )
    full_cover.paste(front_cover, front_cover_position)

    # Load and paste the logo on the back cover
    logo_path = os.path.join(os.path.dirname(__file__), "resources", "logo.jpg")
    logo = Image.open(logo_path)
    logo_size = int(
        2 * inch / 3
    )  # Set logo size to 2/3 inch (1/3 of original 2 inches)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    # Calculate logo position (centered horizontally, 1 inch from bottom)
    logo_x = int(wrap_margin + (cover_width - logo_size) / 2)
    logo_y = int(total_height - wrap_margin - bleed_margin - logo_size - inch)

    full_cover.paste(logo, (logo_x, logo_y))

    # Create the PDF
    c = canvas.Canvas(output_path, pagesize=(total_width, total_height))

    # Draw the full cover image
    c.drawInlineImage(full_cover, 0, 0, total_width, total_height)

    # Add spine text here if the page_count is over 80
    if page_count > 80:
        # Register the font (assuming SF-Pro.ttf is in the same directory as the script)
        pdfmetrics.registerFont(TTFont("SF-Pro", "SF-Pro.ttf"))
        c.setFont("SF-Pro", 12)

        # Calculate the position for the spine text.
        # -bleed_margin is to account for the bleed margin on the right side of the spine
        spine_center_x = wrap_margin + cover_width - bleed_margin + (spine_width / 2)
        spine_center_y = total_height / 2

        # Save the current state
        c.saveState()

        # Translate to the spine center, rotate, and draw the text
        c.translate(spine_center_x, spine_center_y)
        c.rotate(-90)
        text_width = c.stringWidth(book_title, "SF-Pro", 12)
        c.drawString(-text_width / 2, 0, book_title)

        # Restore the previous state
        c.restoreState()

    c.showPage()
    c.save()
