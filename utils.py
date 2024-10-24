import asyncio
import os

from pdf2image import convert_from_path


async def save_image(image, save_path):
    """Save an image asynchronously.

    Args:
        image: PIL Image - The Image object to save.
        save_path: str - The path to save the image to.
    """
    await asyncio.to_thread(image.save, save_path, 'PNG')


async def save_pdf_as_images(pdf_path, output_folder, dpi=200):
    """Given a PDF file path convert and save its pages as images.

    Args:
        pdf_path: str - Path to the PDF file.
        output_folder: str - Path of folter to save images to.
        dpi: int - Capture resolution. Default 200.
    """
    images = await asyncio.to_thread(convert_from_path, pdf_path, dpi=dpi)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    save_tasks = []
    pages = []
    for i, image in enumerate(images):
        page_number = i + 1
        output_image_path = os.path.join(output_folder, f'{page_number}.png')
        pages.append(
            {
                'number': page_number,
                'filepath': output_image_path,
            }
        )
        save_tasks.append(save_image(image, output_image_path))

    await asyncio.gather(*save_tasks)

    return pages
