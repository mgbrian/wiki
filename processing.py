import asyncio
import os
import uuid

import aiofiles
import magic

from db.models import Document, Page
import utils


UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'media/'
)


class UnsupportedFileType(Exception):
    """Exception type for uploaded files that are not of a supported type."""
    pass


# These are separate from the async processor because
# the file pointer gets lost somehow if they're in the DocumentProcessor class.
# In any case this is pre-processing...
async def get_file_type(file):
    """Figure out file type."""
    mime = magic.Magic(mime=True)
    # Read small chunk to detect mimetype
    file_type = mime.from_buffer(file.read(1024))
    file.seek(0)

    if file_type == 'application/pdf':
        return 'pdf'

    elif file_type.startswith('image/'):
        # TODO: Perhaps standardize image params e.g. resolution, size limits, etc.
        # Do this for both PDF pages and standalone images.
        return 'image'

    else:
        raise UnsupportedFileType('File must be a pdf or image.')


async def save_file(file):
    """Asynchronously save a file to the filesystem.

    Args:
        file: File - The file to save.

    Returns:
        dict: Dictionary with filename and path
    """
    # TODO: Take care of filename collisions in the filesystem.
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(file.read())

    return {'filename': filename, 'filepath': filepath}


class DocumentProcessor():
    """End to end async processor for documents (files).

    A document processor instance takes a single document and sees it through
    the entire processing pipeline.
    """
    def __init__(self, document):
        """
        Args:
            file: file - A file to process.
            document: models.Document - The document to process.
        """
        self.document = document

    async def process(self):
        """
        Processing Pipeline:
        --------------------
        1. Split file into pages if necessary
        2. Save pages to DB
        3. Parse pages
        """
        if self.document.type == 1:  # 'pdf'
            pages_info = await self.split_pdf(self.document.filepath)
            await self.save_pages_to_db(self.document, pages_info)

        elif self.document.type == 2:  # 'image'
            _ = await Page.objects.acreate(
                document=self.document,
                number=1,
                filepath=self.document.filepath
            )

    async def split_pdf(self, filepath):
        """Split a pdf file into separate pages and save them as images.

        Args:
            filepath: str - Path to the file to split.

        Returns:
            list of dict: List of dictionaries, each with a page's info:
                number and filepath.
        """
        pages_folder = os.path.join(os.path.dirname(filepath), self.document.id)

        return await utils.save_pdf_as_images(filepath, pages_folder)

    async def save_pages_to_db(self, document, pages_info):
        """Split a pdf file into separate pages and save them as images.

        Args:
            document: models.Document - The Document.
            pages_info: list of dict - List of dictionaries, each with a page's
                info number and filepath.

        Returns:
            list of dict: List of dictionaries, each with a page's info:
                number and filepath.
        """
        for page_info in pages_info:
            # TODO: Handle case where page save fails.
            page_creation_task = asyncio.create_task(
                Page.objects.acreate(
                    document=document,
                    number=page_info['number'],
                    filepath=page_info['filepath']
                )
            )

    async def parse_pages(self):
        pass


class DocumentProcessorQueue():
    """Queue for processing documents."""
    def __init__(self):
        self.queue = asyncio.Queue()
        self.processing_task = None

    async def enqueue(self, document):
        """Add a document processor to the queue.

        Args:
            file: file - A file to process.
            id: str - A unique id for the document. Optional. If none is provided
                one will be generated.
        """
        processor = DocumentProcessor(document)
        await self.queue.put(processor)

        # Ensure the processing loop is running (in case it was idle).
        if self.processing_task is None or self.processing_task.done():
            self.processing_task = asyncio.create_task(self.process_queue())

    async def process_queue(self):
        while not self.queue.empty():
            processor = await self.queue.get()

            try:
                await processor.process()

            except Exception as e:
                # print(e)
                raise
                pass

            finally:
                self.queue.task_done()


document_processor_queue = DocumentProcessorQueue()
