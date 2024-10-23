from pdf2image import convert_from_path
import os


def save_pdf_as_images(pdf_path, output_folder, dpi=200):
    """Given a PDF file path convert and save its pages as images.

    Args:
        pdf_path: str - Path to the PDF file.
        output_folder: str - Path of folter to save images to.
        dpi: int - Capture resolution. Default 200.
    """
    images = convert_from_path(pdf_path, dpi=dpi)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for i, image in enumerate(images):
        output_image_path = os.path.join(output_folder, f'{i+1}.png')
        image.save(output_image_path, 'PNG')
