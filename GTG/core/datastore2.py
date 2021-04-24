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

"""The datastore ties together all the basic type stores and backends."""

import logging
from time import time

from GTG.core.tasks2 import TaskStore
from GTG.core.tags2 import TagStore
from GTG.core.saved_searches import SavedSearchStore

from lxml import etree as et


log = logging.getLogger(__name__)


class Datastore2:

    def __init__(self) -> None:
        self.tasks = TaskStore()
        self.tags = TagStore()
        self.saved_searches = SavedSearchStore()
        self.xml_tree = None


    def load_data(self, data: et.Element) -> None:

        self.saved_searches.from_xml(data.find('searchlist'))
        self.tags.from_xml(data.find('taglist'))
        self.tasks.from_xml(data.find('tasklist'), self.tags)


    def load_file(self, path: str) -> None:

        if log.isEnabledFor(logging.DEBUG):
            bench_start = time()

        parser = et.XMLParser(remove_blank_text=True, strip_cdata=False)

        with open(path, 'rb') as stream:
            self.tree = et.parse(stream, parser=parser)
            self.load_data(self.tree)

        if log.isEnabledFor(logging.DEBUG):
            log.debug('Processed file %s in %.2fms',
                      path, (time() - bench_start) * 1000)


    def generate_xml(self) -> et.ElementTree:

        root = et.Element('gtgData')
        root.set('appVersion', '0.5')
        root.set('xmlVersion', '2')

        root.append(self.tags.to_xml())
        root.append(self.saved_searches.to_xml())
        root.append(self.tasks.to_xml())

        return et.ElementTree(root)


    def save_file(self, path: str) -> None:

        if log.isEnabledFor(logging.DEBUG):
            bench_start = time()

        tree = self.generate_xml()

        with open(path, 'wb') as stream:
            tree.write(stream, xml_declaration=True,
                    pretty_print=True,
                    encoding='UTF-8')

        if log.isEnabledFor(logging.DEBUG):
            log.debug('Processed file %s in %.2fms',
                      path, (time() - bench_start) * 1000)


    def print_info(self) -> None:
        ...
