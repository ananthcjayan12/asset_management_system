from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('assets','0001_initial'),('core','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='AssetMovement', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
        ('movement_type', models.CharField(choices=[('INITIAL_ASSIGNMENT','Initial assignment'),('TRANSFER','Transfer'),('RETURN','Return'),('GATE_OUT','Gate outward'),('GATE_IN','Gate inward'),('DISPOSAL','Disposal')], max_length=30)),
        ('voucher_number', models.CharField(blank=True, max_length=100)), ('movement_date', models.DateField()), ('remarks', models.TextField(blank=True)),
        ('transfer', models.BooleanField(default=False)), ('transfer_from_name', models.CharField(blank=True, max_length=150)), ('transfer_from_id', models.CharField(blank=True, max_length=50)),
        ('transfer_to_id', models.CharField(blank=True, max_length=50)), ('transfer_to_name', models.CharField(blank=True, max_length=150)), ('transfer_voucher_date', models.DateField(blank=True, null=True)),
        ('returned_stock', models.BooleanField(default=False)), ('return_from_name', models.CharField(blank=True, max_length=150)), ('return_voucher_date', models.DateField(blank=True, null=True)),
        ('return_clause', models.TextField(blank=True)),
        ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_movements', to=settings.AUTH_USER_MODEL)),
        ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movements', to='assets.asset')),
        ('from_employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movements_from', to='core.employee')),
        ('from_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movements_from', to='core.location')),
        ('return_from_division', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.division')),
        ('to_employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movements_to', to='core.employee')),
        ('to_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movements_to', to='core.location')),
    ], options={'ordering':['-movement_date','-created_at'], 'permissions':[('approve_assetmovement','Can approve and execute asset movements')]})]
