# Generated by Django 4.2 on 2024-10-26 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0008_enable_pgvector'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='type',
            field=models.IntegerField(choices=[(0, 'unknown'), (1, 'pdf'), (2, 'image'), (3, 'text')], default=0),
        ),
    ]
