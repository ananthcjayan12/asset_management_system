from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('assets','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='ImportBatch', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('uploaded_file', models.FileField(upload_to='imports/%Y/%m/')), ('status', models.CharField(choices=[('UPLOADED','Uploaded'),('VALIDATED','Validated'),('COMPLETED','Completed'),('FAILED','Failed')], default='UPLOADED', max_length=20)),
            ('total_rows', models.PositiveIntegerField(default=0)), ('valid_rows', models.PositiveIntegerField(default=0)), ('invalid_rows', models.PositiveIntegerField(default=0)),
            ('completed_at', models.DateTimeField(blank=True, null=True)), ('notes', models.TextField(blank=True)),
            ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ], options={'ordering':['-created_at']}),
        migrations.CreateModel(name='ImportRow', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('row_number', models.PositiveIntegerField()), ('original_data', models.JSONField(default=dict)),
            ('validation_status', models.CharField(choices=[('VALID','Valid'),('INVALID','Invalid'),('IMPORTED','Imported')], max_length=20)),
            ('validation_errors', models.JSONField(blank=True, default=list)),
            ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rows', to='imports_app.importbatch')),
            ('created_asset', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='assets.asset')),
        ], options={'ordering':['row_number']}),
        migrations.AddConstraint(model_name='importrow', constraint=models.UniqueConstraint(fields=('batch','row_number'), name='unique_import_row')),
    ]
