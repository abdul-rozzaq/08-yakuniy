# Generated by Django 5.1.3 on 2024-11-29 21:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0002_course_lesson_comment_rating'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rating',
            old_name='user',
            new_name='creator',
        ),
    ]
