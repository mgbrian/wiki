import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from asgiref.sync import async_to_sync
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import ollama
from pgvector.django import VectorField, HnswIndex

from image import Image
from parser import parse_page_image

# TODO: Might want to consider using asyncio.to_thread for page parsing
# to improve readability.
page_parser_executor = ThreadPoolExecutor(max_workers=5)


def documents_path():
    return os.path.abspath(os.path.join(settings.BASE_DIR, '../media'))


DOCUMENT_STATUS_CODES = (
    (0, "Processing"),
    (1, "Ready"),
    (2, "Error"),
)

PAGE_STATUS_CODES = (
    (0, "Processing"),
    (1, "Ready"),
    (2, "Error"),
)


class Document(models.Model):
    name = models.CharField(max_length=255)
    filepath = models.FilePathField(path=documents_path)
    summary = models.TextField()
    status = models.IntegerField(choices=DOCUMENT_STATUS_CODES, default=0)


class Page(models.Model):
    document = models.ForeignKey('Document', on_delete=models.CASCADE,
        related_name='pages',)
    number = models.IntegerField()
    previous = models.OneToOneField('Page', on_delete=models.CASCADE,
        related_name='next', blank=True, null=True)
    filepath = models.FilePathField(path=documents_path, recursive=True)
    text = models.TextField(null=True, blank=True)
    text_embeddings = VectorField(dimensions=768, blank=True, null=True)
    summary = models.TextField(null=True, blank=True)
    summary_embeddings = VectorField(dimensions=768, blank=True, null=True)
    # Different from summary -- think of this as similar to alt text explaining
    # what is on the page. summary and text may be blank if the page doesn't contain
    # anything.
    description = models.TextField(null=True, blank=True)
    description_embeddings = VectorField(dimensions=768, blank=True, null=True)
    status = models.IntegerField(choices=PAGE_STATUS_CODES, default=0)
    error_details = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['document', 'number']
        indexes = [
            HnswIndex(
                name="text_embeddings_index",
                fields=["text_embeddings"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            ),
            HnswIndex(
                name="description_embeddings_index",
                fields=["description_embeddings"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            ),
            HnswIndex(
                name="summary_embeddings_index",
                fields=["summary_embeddings"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            )
        ]

    def save(self, *args, **kwargs):
        # Presumably we're not going to be saving often, so OK to just
        # calculate these without checking whether the underlying text has
        # changed.
        self.text_embeddings = calculate_embeddings(self.text)
        self.summary_embeddings = calculate_embeddings(self.summary)
        self.description_embeddings = calculate_embeddings(self.description)

        super().save(*args, **kwargs)

    async def asave(self, *args, **kwargs):
        self.text_embeddings = await asyncio.to_thread(calculate_embeddings, self.text)
        self.summary_embeddings = await asyncio.to_thread(calculate_embeddings, self.summary)
        self.description_embeddings = await asyncio.to_thread(calculate_embeddings, self.description)

        await super().asave(*args, **kwargs)


class Proposition(models.Model):
    # https://arxiv.org/pdf/2312.06648
    # https://github.com/langchain-ai/langchain/blob/master/templates/propositional-retrieval/propositional_retrieval/proposal_chain.py
    # summary, start_page, end_page
    pass


class User(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)


@receiver(post_save, sender=Page)
def parse_page(sender, instance, created, **kwargs):
    """Parse a Page on creation."""
    if created:
        def _parse_image():
            try:
                page_image = Image(instance.filepath)
                parse_result = parse_page_image(page_image)

                instance.text = parse_result['text']
                instance.summary = parse_result['summary']
                instance.description = parse_result['description']
                instance.status = 1
                instance.save()

            # TODO: Catch more specific Exceptions here.
            except Exception as e:
                instance.status = 2
                instance.error_details = f'{type(e)}: {e}'
                instance.save()
                # Update document status to "error""
                # TODO: Figure out more DRY way to do this.
                instance.document.status = 2
                instance.document.save()

        page_parser_executor.submit(_parse_image)


def calculate_embeddings(text):
    """Calculate 768-dimension embeddings for the given text.

    Args:
        text: str - The text to embed.

    Returns:
        TODO: Confirm Nomic returns this.
        For symmetry: https://github.com/pgvector/pgvector-python/blob/master/pgvector/django/vector.py
        np.array of np.float32
        list of float - 768-dimensions embeddings for the given text, or None if
            text is None/the empty string.
    """
    if not text:
        return None
    # This calls this:
    # https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
    # TODO: Pull embeddings model in install script.
    api_response = ollama.embed(model="nomic-embed-text", input=text)
    embeddings_list = api_response.get('embeddings')

    # TODO: Find out if there are any non-error situation where embeddings are
    # not returned. If not, raise an error here instead of returning None.
    return embeddings_list[0] if embeddings_list else None
