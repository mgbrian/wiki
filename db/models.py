import os

from django.conf import settings
from django.db import models


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
    summary = models.TextField(null=True, blank=True)
    # Different from summary -- think of this as similar to alt text explaining
    # what is on the page. summary and text may be blank if the page doesn't contain
    # anything.
    description = models.TextField(null=True, blank=True)
    status = models.IntegerField(choices=PAGE_STATUS_CODES, default=0)


class Proposition(models.Model):
    # https://arxiv.org/pdf/2312.06648
    # https://github.com/langchain-ai/langchain/blob/master/templates/propositional-retrieval/propositional_retrieval/proposal_chain.py
    # summary, start_page, end_page
    pass
