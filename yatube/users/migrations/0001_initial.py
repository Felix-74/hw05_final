from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChangePasswordAfterReset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('new_pass', models.CharField(max_length=50)),
                ('new_pass_confirm', models.CharField(max_length=50)),
            ],
        ),
    ]
