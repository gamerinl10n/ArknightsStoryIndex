"""Synthetic fixtures only: structural eligibility must not imply semantic accuracy."""
import unittest
from scripts.audit_alignment import structure


class AlignmentAuditTests(unittest.TestCase):
    def test_localized_text_is_ignored_but_branch_and_scene_are_not(self):
        a = '[background(image="scene_a")]\n[name="阿米娅"]示例\n[predicate(references="1")]'
        b = '[background(image="scene_a")]\n[name="아미야"]합성 예문\n[predicate(references="1")]'
        self.assertEqual(structure(a)[0], structure(b)[0])
        self.assertNotEqual(structure(a)[0], structure(b.replace('scene_a', 'scene_b'))[0])
        self.assertNotEqual(structure(a)[0], structure(b.replace('references="1"', 'references="2"'))[0])

    def test_inserted_commands_and_multiline_ids_are_not_lost(self):
        a = '[multiline(name="A", id="1")]Synthetic fixture'
        self.assertNotEqual(structure(a)[0], structure(a.replace('id="1"', 'id="2"'))[0])
        self.assertNotEqual(structure(a)[0], structure('[delay(time=1)]\n' + a)[0])

    def test_attribute_inventory_is_names_only(self):
        _, attrs = structure('[name="Synthetic person"]Synthetic text')
        self.assertEqual(dict(attrs), {'name': 1})

    def test_sticker_identity_names_are_not_treated_as_localized_speakers(self):
        a = '[sticker(name="scene_a",text="Synthetic")]'
        b = '[sticker(name="scene_b",text="Translation")]'
        self.assertNotEqual(structure(a)[0], structure(b)[0])


if __name__ == '__main__':
    unittest.main()
