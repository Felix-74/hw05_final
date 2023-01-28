from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0007_post_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
    ]
