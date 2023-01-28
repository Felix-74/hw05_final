from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0006_delete_post_create'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='Картинка'),
        ),
    ]
