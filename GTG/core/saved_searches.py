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

from uuid import uuid4
from dataclasses import dataclass, field
import logging

from lxml.etree import Element, SubElement
from typing import List

from GTG.core.base_store import BaseStore

log = logging.getLogger(__name__)


@dataclass
class SavedSearch:
    """A saved search."""

    id: uuid4
    name: str
    query: str
    icon: str = None
    children: List = field(default_factory=list)

    def __str__(self) -> str:
        """String representation."""

        return (f'Saved Search "{self.name}" '
                f'with query "{self.query}" and id "{self.id}"')


class SavedSearchStore(BaseStore):
    """A list of saved searches."""

    #: Tag to look for in XML
    XML_TAG = 'savedSearch'


    def __init__(self) -> None:
        self.lookup = {}
        self.data = []


    def __str__(self) -> str:
        """String representation."""

        return f'Saved Search Store. Holds {len(self.lookup)} search(es)'


    def from_xml(self, xml: Element) -> 'SavedSearchStore':
        """Load searches from an LXML element."""

        elements = list(xml.iter(self.XML_TAG))

        # Do parent searches first
        for element in elements.copy():
            parent = element.get('parent')

            # Note: Previous versions of GTG stored saved searches as
            # tags with a "search" parent, and this stuck for a while
            # after the file format changed.
            if parent and parent != 'search':
                continue

            search_id = element.get('id')
            name = element.get('name')
            query = element.get('query')

            search = SavedSearch(id=search_id, name=name, query=query)

            self.add(search)
            log.debug('Added %s', search)
            elements.remove(element)


        # Now the remaining searches are children
        for element in elements:
            parent = element.get('parent')
            search_id = element.get('id')
            name = element.get('name')
            query = element.get('query')

            search = SavedSearch(id=search_id, name=name, query=query)
            self.add(search, parent)
            log.debug('Added %s as child of %s', search, parent)


    def to_xml(self) -> Element:
        """Save searches to an LXML element."""

        root = Element('SavedSearches')

        parent_map = {}

        for search in self.data:
            for child in search.children:
                parent_map[child.id] = search.id

        for search in self.lookup.values():
            element = SubElement(root, self.XML_TAG)
            element.set('id', str(search.id))
            element.set('name', search.name)
            element.set('query', search.query)

            try:
                element.set('parent', str(parent_map[search.id]))
            except KeyError:
                pass

        return root


    def new(self, name: str, query: str, parent: uuid4 = None) -> SavedSearch:
        """Create a new saved search and add it to the store."""

        search_id = uuid4()
        search = SavedSearch(id=search_id, name=name, query=query)

        if parent:
            self.add(search, parent)
        else:
            self.data.append(search)
            self.lookup[search_id] = search

        return search
