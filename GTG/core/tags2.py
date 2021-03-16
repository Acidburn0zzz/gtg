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

from gi.repository.Gdk import Color

from uuid import uuid4
from dataclasses import dataclass, field
import logging
import random

from lxml.etree import Element, SubElement
from typing import List

from GTG.core.base_store import BaseStore

log = logging.getLogger(__name__)


@dataclass
class Tag2:
    """A tag that can be applied to a Task."""

    id: uuid4
    name: str
    icon: str = None
    color: str = None
    actionable: bool = True
    children: List = field(default_factory=list)

    def __str__(self) -> str:
        """String representation."""

        return (f'Tag "{self.name}" with id "{self.id}"')


class TagStore(BaseStore):
    """A list of tags."""

    #: Tag to look for in XML
    XML_TAG = 'tag'


    def __init__(self) -> None:
        self.used_colors = set()
        super().__init__()


    def __str__(self) -> str:
        """String representation."""

        return f'Tag Store. Holds {len(self.lookup)} tag(s)'


    def get(self, name: str) -> Tag2:
        """Get a tag by name."""

        return self.lookup[name]


    def new(self, name: str, parent: uuid4 = None) -> Tag2:
        """Create a new tag and add it to the store."""

        name = name if not name.startswith('@') else name[1:]

        try:
            return self.lookup[name]
        except KeyError:
            tid = uuid4()
            tag = Tag2(id=tid, name=name)

            if parent:
                self.add(tag, parent)
            else:
                self.data.append(tag)
                self.lookup[tid] = tag

            return tag

    def from_xml(self, xml: Element) -> 'SavedSearchStore':
        """Load searches from an LXML element."""

        elements = list(xml.iter(self.XML_TAG))

        # Do parent searches first
        for element in elements.copy():
            parent = element.get('parent')

            if parent:
                continue

            tid = element.get('id')
            name = element.get('name')
            color = element.get('color')
            icon = element.get('icon')

            tag = Tag2(id=tid, name=name, color=color, icon=icon)
            self.add(tag)

            log.debug('Added %s', tag)
            elements.remove(element)


        # Now the remaining searches are children
        for element in elements:
            parent = element.get('parent')
            tid = element.get('id')
            name = element.get('name')
            color = element.get('color')
            icon = element.get('icon')

            tag = Tag2(id=tid, name=name, color=color, icon=icon)
            self.add(tag, parent)

            log.debug('Added %s as child of %s', tag, parent)


    def to_xml(self) -> Element:
        """Save searches to an LXML element."""

        root = Element('SavedSearches')

        parent_map = {}

        for tag in self.data:
            for child in tag.children:
                parent_map[child.id] = tag.id

        for tag in self.lookup.values():
            element = SubElement(root, self.XML_TAG)
            element.set('id', str(tag.id))
            element.set('name', tag.name)

            if tag.color:
                element.set('color', tag.color)

            if tag.icon:
                element.set('icon', tag.icon)

            try:
                element.set('parent', str(parent_map[tag.id]))
            except KeyError:
                pass

        return root


    def generate_color(self) -> Color:
        """Generate a random color that isn't already used."""

        MAX_VALUE = 65535
        color = None

        while color in self.used_colors:
            color = Color(
                random.randint(0, MAX_VALUE),
                random.randint(0, MAX_VALUE),
                random.randint(0, MAX_VALUE)
            ).to_string()

        self.used_colors.add(color)
        return color
