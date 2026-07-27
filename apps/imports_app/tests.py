from django.test import TestCase
from .services import normalize_row
class ImportTests(TestCase):
    def test_header_aliases(self):
        data = normalize_row({"Transaction ID": "T1", "Brief Description": "Laptop", "Room No": "10"})
        self.assertEqual(data["TRANSACTION_ID"], "T1")
        self.assertEqual(data["BRIEF_DESCRIPTION"], "Laptop")
        self.assertEqual(data["ROOM_NO"], "10")
