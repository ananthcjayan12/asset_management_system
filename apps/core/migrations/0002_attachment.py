from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('assets','0001_initial'), ('core','0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='Attachment', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
        ('title', models.CharField(max_length=150)), ('file', models.FileField(upload_to='asset_attachments/%Y/%m/')),
        ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='assets.asset')),
        ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
    ])]
