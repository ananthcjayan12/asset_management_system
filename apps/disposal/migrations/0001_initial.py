from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('assets','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='DisposalRecord', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
        ('status', models.CharField(choices=[('PROPOSED','Proposed'),('APPROVED','Approved'),('AUCTIONED','Auctioned'),('WRITTEN_OFF','Written off'),('PASSED_OUT','Passed out')], default='PROPOSED', max_length=30)),
        ('lot_name', models.CharField(blank=True, max_length=150, verbose_name='Disposal details / lot name')), ('disposal_file_no', models.CharField(blank=True, max_length=100)),
        ('auction_id', models.CharField(blank=True, max_length=100)), ('h1_buyer', models.CharField(blank=True, max_length=200)),
        ('emd_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)), ('total_book_value', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
        ('financial_year', models.CharField(blank=True, max_length=20)), ('realized_sale_value', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
        ('apportioned_sale_value', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)), ('write_off_om_no', models.CharField(blank=True, max_length=100)),
        ('write_off_om_date', models.DateField(blank=True, null=True)), ('passout_for', models.CharField(blank=True, max_length=150)), ('passout_type', models.CharField(blank=True, max_length=100)),
        ('passout_no', models.CharField(blank=True, max_length=100)), ('passout_date', models.DateField(blank=True, null=True)), ('remarks', models.TextField(blank=True)),
        ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ('asset', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='disposal_record', to='assets.asset')),
    ], options={'ordering':['-created_at'], 'permissions':[('approve_disposalrecord','Can approve disposal and write-off')]})]
