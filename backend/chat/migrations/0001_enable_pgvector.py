from django.db import migrations
from pgvector.django import VectorExtension

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # migrations.RunSQL(
        #     "CREATE EXTENSION IF NOT EXISTS vector;",
        #     "DROP EXTENSION IF EXISTS vector;"
        # ),
        VectorExtension(),
    ]