import json

from django.core.management.base import BaseCommand

from apps.core.demo_data import cleanup_demo_data


class Command(BaseCommand):
    help = "Remove only temporary records and users created by the Playwright demo suite."

    def add_arguments(self, parser):
        parser.add_argument("--keep-users", action="store_true")
        parser.add_argument("--json", action="store_true", dest="as_json")

    def handle(self, *args, **options):
        result = cleanup_demo_data(delete_users=not options["keep_users"])
        if options["as_json"]:
            self.stdout.write(json.dumps(result, indent=2))
        else:
            self.stdout.write(self.style.SUCCESS(f"Playwright demo cleanup completed: {result}"))
