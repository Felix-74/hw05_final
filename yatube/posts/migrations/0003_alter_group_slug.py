from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0002_group_alter_post_pub_date_post_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(max_length=255, verbose_name='slug'),
        ),
    ]
