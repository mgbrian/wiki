import os

from django.conf import settings
from django.db import models


def documents_path():
    return os.path.abspath(os.path.join(settings.BASE_DIR, '../media'))


def document_pages_path():
    # TODO: Decide structure.
    return ''


class Document(models.Model):
    name = models.CharField(max_length=255)
    filepath = models.FilePathField(path=documents_path)
    contents_summary = models.TextField()


class Page(models.Model):
    document = models.ForeignKey('Document', on_delete=models.CASCADE,
        related_name='pages',)
    number = models.IntegerField()
    previous = models.OneToOneField('Page', on_delete=models.CASCADE,
        related_name='next', blank=True, null=True)
    filepath = models.FilePathField(path=document_pages_path)
    contents_summary = models.TextField()


class Proposition(models.Model):
    # https://arxiv.org/pdf/2312.06648
    # https://github.com/langchain-ai/langchain/blob/master/templates/propositional-retrieval/propositional_retrieval/proposal_chain.py
    # summary, start_page, end_page
    pass
