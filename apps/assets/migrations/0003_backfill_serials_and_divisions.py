from django.db import migrations
from django.db.models import Max


def forwards(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    Asset.objects.filter(asset_code="").update(asset_code=None)
    next_sl = (Asset.objects.aggregate(m=Max("sl_no"))["m"] or 0) + 1
    for asset in Asset.objects.filter(sl_no__isnull=True).order_by("id"):
        asset.sl_no = next_sl
        next_sl += 1
        asset.save(update_fields=["sl_no"])
    for asset in Asset.objects.filter(division__isnull=True).select_related("current_custodian", "current_location"):
        division_id = getattr(asset.current_custodian, "division_id", None) or getattr(asset.current_location, "division_id", None)
        if division_id:
            asset.division_id = division_id
            asset.save(update_fields=["division"])


class Migration(migrations.Migration):
    dependencies = [("assets", "0002_alter_asset_options_asset_division_and_more")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
