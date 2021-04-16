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

from GTG.core.tasks2 import TaskStore
from GTG.core.tags2 import TagStore
from GTG.core.saved_searches import SavedSearchStore

from lxml.etree import Element


log = logging.getLogger(__name__)


class Datastore2:

    def __init__(self) -> None:
        self.tasks = TaskStore()
        self.tags = TagStore()
        self.saved_searches = SavedSearchStore()


    def load_data(self, data: str) -> None:
        ...


    def load_file(self, path: str) -> None:
        ...


    def generate_xml(self) -> Element:
        ...


    def save_file(self, path: str) -> None:
        ...
