import asyncio
import os
import uuid

import aiofiles
from db.models import Document
import magic


UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'media/'
)


class UnsupportedFileType(Exception):
    """Exception type for uploaded files that are not of a supported type."""
    pass


class DocumentProcessor():
    """End to end async processor for documents (files).

    A document processor instance takes a single document and sees it through
    the entire processing pipeline.
    """
    def __init__(self, file, document_id=None):
        """
        Args:
            file: file - A file to process.
            document_id: str - A unique id for the document.
                Optional. If none is provided one will be generated.
        """
        self.document_id = str(id) or str(uuid.uuid4())
        self.file = file

    async def process(self):
        """
        Processing Pipeline:
        --------------------
        0. Confirm file is of the right type (do this here and not in routes
                in case we're bypassing the web uploader)
        1. Save file to filesystem
        2. Create DB entry for document
        3. Split file into pages if necessary
        4. Parse pages
        """
        pass

    async def get_file_type(self):
        """Figure out file type."""
        mime = magic.Magic(mime=True)
        # Read small chunk to detect mimetype
        file_type = mime.from_buffer(self.file.read(1024))
        self.file.seek(0)

        if file_type == 'application/pdf':
            return 'pdf'

        elif file_type.startswith('image/'):
            # TODO: Perhaps standardize image params e.g. resolution, size limits, etc.
            # Do this for both PDF pages and standalone images.
            return 'image'

        else:
            raise UnsupportedFileType('File must be a pdf or image.')

    async def save_file(self):
        """Save file to filesystem.

        Returns:
            dict: Dictionary with filename and path
        """
        # TODO: Take care of filename collisions in the filesystem.
        filename = self.file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(self.file.read())

        return {'filename': filename, 'filepath': filepath}

    async def save_to_db(self, filename, filepath, document_type):
        """Save Document to database.

        Returns:
            Document: The created document object.
        """
        # TODO: Take care of unlikely event that there is a Document already
        # with the same id.
        document = await Document.objects.acreate(
            id=self.document_id,
            name=filename,
            filepath=filepath,
            type=document_type
        )

        return document

    async def split_document(self):
        pass

    async def parse_pages(self):
        pass


class DocumentProcessorQueue():
    """Queue for processing documents."""
    def __init__(self):
        self.queue = asyncio.Queue()
        self.processing_task = None

    async def enqueue(self, file, id=None):
        """Add a document processor to the queue.

        Args:
            Args:
                file: file - A file to process.
                id: str - A unique id for the document. Optional. If none is provided
                    one will be generated.
        """
        processor = DocumentProcessor(file, id)
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
                pass

            finally:
                self.queue.task_done()


document_processor_queue = DocumentProcessorQueue()
