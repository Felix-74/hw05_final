from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0005_auto_20221201_0117'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Post_create',
        ),
    ]
