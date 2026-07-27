import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('core','0001_initial')]
    operations = [
        migrations.CreateModel(name='Asset', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('asset_code', models.CharField(max_length=50, unique=True)), ('sl_no', models.PositiveIntegerField(blank=True, null=True, verbose_name='SL No.')),
            ('transaction_id', models.CharField(max_length=100, unique=True)), ('nc_no', models.CharField(blank=True, max_length=100, verbose_name='NC No.')),
            ('nc_date', models.DateField(blank=True, null=True, verbose_name='NC date')), ('brief_description', models.CharField(max_length=250)),
            ('specification', models.TextField(blank=True)), ('make', models.CharField(blank=True, max_length=150)), ('model', models.CharField(blank=True, max_length=150)),
            ('item_sl_no', models.CharField(blank=True, max_length=150, verbose_name='Item serial no.')),
            ('current_status', models.CharField(choices=[('IN_STOCK','In stock'),('ASSIGNED','Assigned'),('OUTSIDE','Outside premises'),('RETURN_PENDING','Return pending'),('UNDER_DISPOSAL','Under disposal'),('DISPOSED','Disposed'),('WRITTEN_OFF','Written off'),('PASSED_OUT','Passed out')], default='IN_STOCK', max_length=30)),
            ('room_in_charge_name', models.CharField(blank=True, max_length=150)), ('current_user', models.CharField(blank=True, help_text='Free-text legacy/current-user value', max_length=150)),
            ('qr_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)), ('remarks', models.TextField(blank=True)), ('is_active', models.BooleanField(default=True)),
            ('current_custodian', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='assets', to='core.employee')),
            ('current_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='assets', to='core.location')),
        ], options={'ordering':['asset_code'], 'permissions':[('scan_asset','Can scan asset QR pages'),('view_sensitive_asset','Can view sensitive asset details')]}),
        migrations.CreateModel(name='Installation', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('stock_entry_reference', models.CharField(blank=True, max_length=150)), ('date_of_installation', models.DateField(blank=True, null=True)),
            ('warranty_period_months', models.PositiveIntegerField(blank=True, null=True)), ('status_of_asset', models.CharField(blank=True, max_length=100)),
            ('asset', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='installation', to='assets.asset')),
        ]),
        migrations.CreateModel(name='Procurement', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('qty', models.PositiveIntegerField(default=1)), ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
            ('po_no', models.CharField(blank=True, max_length=100)), ('po_date', models.DateField(blank=True, null=True)),
            ('bill_no', models.CharField(blank=True, max_length=100)), ('bill_date', models.DateField(blank=True, null=True)), ('bill_value', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
            ('asset', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='procurement', to='assets.asset')),
            ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='procurements', to='core.supplier')),
        ]),
    ]
