from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('assets','0001_initial'),('core','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='GatePass', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('gatepass_no', models.CharField(blank=True, max_length=50, unique=True)), ('gatepass_type', models.CharField(choices=[('TEMPORARY','Temporary'),('PERMANENT','Permanent')], max_length=20)),
            ('status', models.CharField(choices=[('REQUESTED','Requested'),('STORES_APPROVED','Stores approved'),('REJECTED','Rejected'),('OUTWARD','Marked outward'),('INWARD','Marked inward'),('CLOSED','Closed')], default='REQUESTED', max_length=30)),
            ('purpose', models.TextField()), ('destination', models.CharField(blank=True, max_length=250)), ('expected_return_date', models.DateField(blank=True, null=True)),
            ('outward_at', models.DateTimeField(blank=True, null=True)), ('inward_at', models.DateTimeField(blank=True, null=True)), ('remarks', models.TextField(blank=True)),
            ('division', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='gatepasses', to='core.division')),
            ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requested_gatepasses', to=settings.AUTH_USER_MODEL)),
            ('security_in_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='security_in_gatepasses', to=settings.AUTH_USER_MODEL)),
            ('security_out_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='security_out_gatepasses', to=settings.AUTH_USER_MODEL)),
            ('stores_marked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stores_gatepasses', to=settings.AUTH_USER_MODEL)),
        ], options={'ordering':['-created_at'], 'permissions':[('approve_gatepass','Can approve gate passes in stores'),('security_scan_gatepass','Can mark gate pass outward and inward')]}),
        migrations.CreateModel(name='GatePassItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('outward_scanned', models.BooleanField(default=False)), ('inward_scanned', models.BooleanField(default=False)), ('remarks', models.CharField(blank=True, max_length=250)),
            ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gatepass_items', to='assets.asset')),
            ('gatepass', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='gatepasses.gatepass')),
        ]),
        migrations.AddConstraint(model_name='gatepassitem', constraint=models.UniqueConstraint(fields=('gatepass','asset'), name='unique_asset_per_gatepass')),
    ]
