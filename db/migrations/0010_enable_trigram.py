from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0009_document_type'),
    ]

    operations = [
        TrigramExtension(),
    ]
