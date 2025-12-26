# yourapp/migrations/0002_enable_pgvector.py
from django.db import migrations, connection

def enable_pgvector(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

class Migration(migrations.Migration):
    dependencies = [
        ('yourapp', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(enable_pgvector),
    ]
