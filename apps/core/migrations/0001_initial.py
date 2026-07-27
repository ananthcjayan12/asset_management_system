from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Division', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('code', models.CharField(max_length=30, unique=True)), ('name', models.CharField(max_length=150, unique=True)),
        ], options={'ordering': ['name']}),
        migrations.CreateModel(name='Supplier', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('name', models.CharField(max_length=200, unique=True)), ('contact_person', models.CharField(blank=True, max_length=150)),
            ('phone', models.CharField(blank=True, max_length=30)), ('email', models.EmailField(blank=True, max_length=254)), ('address', models.TextField(blank=True)),
        ], options={'ordering': ['name']}),
        migrations.CreateModel(name='AuditEvent', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('action', models.CharField(max_length=80)), ('object_type', models.CharField(max_length=80)),
            ('object_id', models.CharField(blank=True, max_length=80)), ('description', models.TextField()),
            ('metadata', models.JSONField(blank=True, default=dict)), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-created_at']}),
        migrations.CreateModel(name='Section', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('name', models.CharField(max_length=150)),
            ('division', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sections', to='core.division')),
        ], options={'ordering': ['division__name', 'name']}),
        migrations.AddConstraint(model_name='section', constraint=models.UniqueConstraint(fields=('division','name'), name='unique_section_per_division')),
        migrations.CreateModel(name='SubSection', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('name', models.CharField(max_length=150)),
            ('section', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subsections', to='core.section')),
        ], options={'ordering': ['section__division__name', 'section__name', 'name']}),
        migrations.AddConstraint(model_name='subsection', constraint=models.UniqueConstraint(fields=('section','name'), name='unique_subsection_per_section')),
        migrations.CreateModel(name='Location', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('name', models.CharField(max_length=150)), ('room_no', models.CharField(blank=True, max_length=50)),
            ('is_stock_location', models.BooleanField(default=False)), ('is_active', models.BooleanField(default=True)),
            ('division', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='locations', to='core.division')),
            ('section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='locations', to='core.section')),
            ('sub_section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='locations', to='core.subsection')),
        ], options={'ordering': ['name','room_no']}),
        migrations.AddConstraint(model_name='location', constraint=models.UniqueConstraint(fields=('name','room_no'), name='unique_named_room')),
        migrations.CreateModel(name='Employee', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('employee_id', models.CharField(max_length=50, unique=True)), ('name', models.CharField(max_length=150)),
            ('email', models.EmailField(blank=True, max_length=254)), ('is_active', models.BooleanField(default=True)),
            ('division', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='core.division')),
            ('section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='core.section')),
        ], options={'ordering': ['name']}),
    ]
