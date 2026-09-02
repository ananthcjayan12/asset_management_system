import json

from django.core.management.base import BaseCommand

from apps.core.demo_data import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    VIEWER_PASSWORD,
    VIEWER_USERNAME,
    cleanup_demo_data,
    prepare_demo_data,
)


class Command(BaseCommand):
    help = "Create deterministic temporary records and users for the local Playwright feature tour."

    def add_arguments(self, parser):
        parser.add_argument("--admin-username", default=ADMIN_USERNAME)
        parser.add_argument("--admin-password", default=ADMIN_PASSWORD)
        parser.add_argument("--viewer-username", default=VIEWER_USERNAME)
        parser.add_argument("--viewer-password", default=VIEWER_PASSWORD)
        parser.add_argument("--skip-cleanup", action="store_true")
        parser.add_argument("--json", action="store_true", dest="as_json")

    def handle(self, *args, **options):
        if not options["skip_cleanup"]:
            cleanup_demo_data()
        result = prepare_demo_data(
            admin_username=options["admin_username"],
            admin_password=options["admin_password"],
            viewer_username=options["viewer_username"],
            viewer_password=options["viewer_password"],
        )
        if options["as_json"]:
            self.stdout.write(json.dumps(result, indent=2))
        else:
            self.stdout.write(self.style.SUCCESS("Playwright demo data prepared."))
