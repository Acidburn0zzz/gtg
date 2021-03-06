# -----------------------------------------------------------------------------
# Getting Things GNOME! - a personal organizer for the GNOME desktop
# Copyright (c) The GTG Team
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

from unittest import TestCase
from uuid import uuid4

from GTG.core.tags2 import Tag2, TagStore
from lxml.etree import Element, SubElement, XML


class TestTagStore(TestCase):


    def test_new(self):
        store = TagStore()
        tag = store.new('My_tag')

        self.assertEqual(len(store.data), 1)
        self.assertEqual(store.lookup[tag.id], tag)
        self.assertIsInstance(tag, Tag2)

        tag2 = store.new('@a_tag')
        self.assertEqual(len(store.data), 2)
        self.assertEqual(tag2.name, 'a_tag')


    def test_xml_load_simple(self):
        ...

    def test_xml_load_tree(self):
        ...

    def test_xml_load_bad(self):
        ...

    def test_xml_write_simple(self):
        ...

    def test_xml_write_tree(self):
        ...

    def test_random_color(self):
        tag_store = TagStore()

        color1 = tag_store.generate_color()
        color2 = tag_store.generate_color()
        color3 = tag_store.generate_color()

        self.assertEqual(len(tag_store.used_colors), 3)
        self.assertNotEqual(color1, color2)
        self.assertNotEqual(color2, color3)
        self.assertNotEqual(color3, color1)
