from django.db import migrations

CENTRES = ["RCED Kolkata", "RCED Kanpur", "RCED Jalandhar", "RCED Ahmedabad"]


def forwards(apps, schema_editor):
    Centre = apps.get_model("core", "Centre")
    Place = apps.get_model("core", "Place")
    Location = apps.get_model("core", "Location")
    for name in CENTRES:
        Centre.objects.get_or_create(name=name)
    # Existing free-text location names become entries of the "Current place / location" drop-down.
    for location in Location.objects.filter(place__isnull=True):
        location.place, _ = Place.objects.get_or_create(name=location.name)
        location.save(update_fields=["place"])


class Migration(migrations.Migration):
    dependencies = [("core", "0003_budget_budgetclassification_building_centre_place_and_more")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
