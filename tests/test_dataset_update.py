"""Synthetic inventories only; no official dialogue fixtures."""
import copy
import unittest
from scripts.check_dataset_update import compare, LANGUAGES


class DatasetUpdateTest(unittest.TestCase):
    def setUp(self):
        self.before = {lang: {'story.txt': ('old', 100)} for lang in LANGUAGES}
        self.after = {lang: {'story.txt': ('new', 105)} for lang in LANGUAGES}

    def test_valid_growth(self):
        self.assertEqual(compare(self.before, self.after, 'new')['issues'], [])

    def test_language_loss_is_not_hidden_by_growth_elsewhere(self):
        self.after['ja_JP'] = {}
        self.after['zh_CN']['story.txt'] = ('new', 10000)
        self.assertTrue(compare(self.before, self.after, 'new')['issues'])

    def test_missing_files_are_blocked_even_if_totals_grow(self):
        self.after['en_US'] = {'replacement.txt': ('new', 200)}
        self.assertTrue(compare(self.before, self.after, 'new')['issues'])

    def test_stale_revision_and_empty_story_are_blocked(self):
        for row in [('old', 105), ('new', 0), ('new', 79)]:
            with self.subTest(row=row):
                candidate = copy.deepcopy(self.after)
                candidate['ko_KR']['story.txt'] = row
                self.assertTrue(compare(self.before, candidate, 'new')['issues'])
