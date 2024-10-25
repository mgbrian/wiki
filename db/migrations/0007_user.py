# Generated by Django 4.2 on 2024-10-25 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0006_page_error_details'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('is_admin', models.BooleanField(default=False)),
            ],
        ),
    ]
