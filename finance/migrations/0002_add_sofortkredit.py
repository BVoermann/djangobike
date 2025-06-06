# Generated migration for Sofortkredit feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credit',
            name='credit_type',
            field=models.CharField(choices=[('instant', 'Sofortkredit'), ('short', 'Kurzfristig'), ('medium', 'Mittelfristig'), ('long', 'Langfristig')], max_length=20),
        ),
    ]