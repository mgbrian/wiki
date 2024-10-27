import asyncio
import uuid


class DocumentProcessor():
    """End to end async processor for documents (files).

    A document processor instance takes a single document and sees it through
    the entire processing pipeline.
    """
    def __init__(self, file, id=None):
        """
        Args:
            file: file - A file to process.
            id: str - A unique id for the document. Optional. If none is provided
                one will be generated.
        """
        self.id = str(id) or str(uuid.uuid4())
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
