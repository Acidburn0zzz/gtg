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

from abc import ABC, abstractmethod
from uuid import uuid4
from dataclasses import dataclass, field
import logging
import random

from lxml.etree import Element
from typing import List, Any


log = logging.getLogger(__name__)


class BaseStore(ABC):
    """Base class for data stores."""


    def __init__(self) -> None:
        self.lookup = {}
        self.data = []


    # --------------------------------------------------------------------------
    # BASIC MANIPULATION
    # --------------------------------------------------------------------------

    @abstractmethod
    def new(self) -> Any:
        ...


    def get(key: str) -> Any:
        """Get a saved search by id."""

        return self.lookup[key]


    def add(self, item: Any, parent_id: uuid4 = None) -> None:
        """Add an existing search to the store."""

        if item.id in self.lookup.keys():
            log.warn('Failed to add item with id %s, already added!',
                     item.id)

            raise KeyError

        if parent_id:
            try:
                self.lookup[parent_id].children.append(item)

            except KeyError:
                log.warn(('Failed to add item with id %s to parent %s, '
                         'parent not found!'), item.id, parent_id)
                raise

        else:
            self.data.append(item)

        self.lookup[item.id] = item
        log.debug('Added %s', item)


    def remove(self, item_id: uuid4) -> None:
        """Remove an existing search from the store."""

        try:
            for item in self.lookup.values():
                if item.id == item_id:
                    for child in item.children:
                        item.children.remove(child)
                        del self.lookup[child.id]

                    self.data.remove(item)

            del self.lookup[item_id]

            log.debug('Removed item with id %s', item_id)

        except KeyError:
            log.warn('Failed to remove item %s, id not found!', item_id)
            raise


    # --------------------------------------------------------------------------
    # PARENTING
    # --------------------------------------------------------------------------

    def parent(self, item_id: uuid4, parent_id: uuid4) -> None:
        """Add a child to a search."""

        try:
            item = self.lookup[item_id]
        except KeyError:
            raise

        try:
            self.data.remove(item)
            self.lookup[parent_id].children.append(item)
        except KeyError:
            raise


    def unparent(self, item_id: uuid4, parent_id: uuid4) -> None:
        """Remove child search from a parent."""

        for child in self.lookup[parent_id].children:
            if child.id == item_id:
                self.data.append(child)
                self.lookup[parent_id].children.remove(child)
                return

        raise KeyError


    # --------------------------------------------------------------------------
    # SERIALIZING
    # --------------------------------------------------------------------------

    @abstractmethod
    def from_xml(self, xml: Element) -> Any:
        ...


    @abstractmethod
    def to_xml(self) -> Element:
        ...


    # --------------------------------------------------------------------------
    # UTILITIES
    # --------------------------------------------------------------------------

    def count(self, root_only: bool = False) -> int:
        """Count all the searches in the store."""

        if root_only:
            return len(self.data)
        else:
            return len(self.lookup)


    def print_list(self) -> None:
        """Print the entre list of searches."""

        print(self)

        for search in self.lookup.values():
            print((f'- "{search.name}" with query "{search.query}" '
                   f'and id "{search.sid}"'))


    def print_tree(self) -> None:
        """Print the all the searches as a tree."""

        def recursive_print(tree: List, indent: int) -> None:
            """Inner print function. """

            tab =  '   ' * indent if indent > 0 else ''

            for node in tree:
                print(f'{tab} └ {node}')

                if node.children:
                    recursive_print(node.children, indent + 1)

        print(self)
        recursive_print(self.data, 0)
