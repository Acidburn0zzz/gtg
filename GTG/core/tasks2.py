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
import logging
from typing import List
from enum import Enum
import re
import datetime

from lxml.etree import Element, SubElement, CDATA

from GTG.core.base_store import BaseStore
from GTG.core.tags2 import Tag2, TagStore
from GTG.core.dates import Date

log = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# REGEXES
# ------------------------------------------------------------------------------

TAG_REGEX = re.compile(r'^\B\@\w+(\-\w+)*\,+')
SUB_REGEX = re.compile(r'\{\!.+\!\}')


# ------------------------------------------------------------------------------
# TASK STATUS
# ------------------------------------------------------------------------------

class Status(Enum):
    """Status for a task."""

    ACTIVE = 0
    DONE = 1
    DISMISSED = -1


# ------------------------------------------------------------------------------
# TASK
# ------------------------------------------------------------------------------

class Task2:
    """A single task."""

    def __init__(self, id: uuid4, title: str) -> None:
        self.id = id
        self.raw_title = title.strip('\t\n')
        self.content =  ''
        self.tags = []
        self.children = []
        self.status = Status.ACTIVE
        self.parent = None

        self.date_added = Date.no_date()
        self._date_due = Date.no_date()
        self.date_start = Date.no_date()
        self.date_closed = Date.no_date()
        self.date_modified = Date(datetime.datetime.now())


    def toggle_status(self, propagate: bool = True) -> None:
        if self.status == Status.ACTIVE:
            self.status = Status.DONE
            self.date_closed = Date.today()

        else:
            self.status = Status.ACTIVE
            self.date_closed = Date.no_date()

            if self.parent and self.parent.status != Status.ACTIVE:
                self.parent.toggle_status(propagate=False)

        if propagate:
            for child in self.children:
                child.toggle_status()


    def dismiss(self) -> None:
        self.status = Status.DISMISSED

        for child in self.children:
            child.dismiss()

    @property
    def due_date(self) -> str:
        return self._date_due


    @due_date.setter
    def due_date(self, value: Date) -> None:
        self._date_due = value

        if not value or value.is_fuzzy():
            return

        for child in self.children:
            if (child.due_date
               and not child.due_date.is_fuzzy()
               and child.due_date > value):

                child.due_date = value

        if (self.parent
           and self.parent.due_date
           and self.parent.due_date.is_fuzzy()
           and self.parent.due_date < value):
            self.parent.due_date = value


    @property
    def title(self) -> str:
        return self.raw_title


    @title.setter
    def title(self, value) -> None:
        self.raw_title = value.strip('\t\n') or _('(no title)')


    @property
    def excerpt(self) -> str:
        if not self.content:
            return ''

        # Strip tags
        txt = TAG_REGEX.sub('', self.content)

        # Strip subtasks
        txt = SUB_REGEX.sub('', txt)

        # Strip blank lines and set within char limit
        return f'{txt.strip()[:80]}…'


    def add_tag(self, tag: Tag2) -> None:
        if isinstance(tag, Tag2):
            if tag not in self.tags:
                self.tags.append(tag)

                for child in self.children:
                    child.add_tag(tag)
        else:
            raise ValueError


    def remove_tag(self, tag_name: str) -> None:
        for t in self.tags:
            if t.name == tag_name:
                self.tags.remove(t)
                (self.content.replace(f'{tag_name}\n\n', '')
                             .replace(f'{tag_name},', '')
                             .replace(f'{tag_name}', ''))

        for child in self.children:
            child.remove_tag(tag_name)


    @property
    def days_left(self) -> int:
        return self.date_due.days_left()


    def update_modified(self) -> None:
        self.modified = Date(datetime.datetime.now())


    def __str__(self) -> str:
        """String representation."""

        tags = ', '.join([t.name for t in self.tags])
        return (f'Task "{self.title}" with id "{self.id}. "'
                f'Status: {self.status}, tags: {tags}')



# ------------------------------------------------------------------------------
# STORE
# ------------------------------------------------------------------------------

class TaskStore(BaseStore):
    """A list of tasks."""

    #: Tag to look for in XML
    XML_TAG = 'task'


    def __init__(self) -> None:
        super().__init__()


    def __str__(self) -> str:
        """String representation."""

        return f'Task Store. Holds {len(self.lookup)} task(s)'


    def get(self, tid: uuid4) -> Task2:
        """Get a tag by name."""

        return self.lookup[tid]


    def new(self, title: str, parent: uuid4 = None) -> Task2:
        tid = uuid4()
        task = Task2(id=tid, title=title)

        if parent:
            self.add(task, parent)
        else:
            self.data.append(task)
            self.lookup[tid] = task

        return task


    def from_xml(self, xml: Element, tag_store: TagStore) -> None:

        elements = list(xml.iter(self.XML_TAG))

        for element in elements:
            tid = element.get('id')
            title = element.find('title').text
            status = element.get('status')

            task = Task2(id=tid, title=title)

            dates = element.find('dates')

            modified = dates.find('modified').text
            task.date_modified = Date(datetime.datetime.fromisoformat(modified))

            added = dates.find('added').text
            task.date_added = Date(datetime.datetime.fromisoformat(added))

            if status == 'Done':
                task.status = Status.DONE
            elif status == 'Dismissed':
                task.status = Status.DISMISSED

            # Dates
            try:
                closed = Date.parse(dates.find('done').text)
                task.date_closed = closed
            except AttributeError:
                pass

            fuzzy_due_date = Date.parse(dates.findtext('fuzzyDue'))
            due_date = Date.parse(dates.findtext('due'))

            if fuzzy_due_date:
                task.date_due = fuzzy_due_date
            elif due_date:
                task.date_due = due_date

            fuzzy_start = dates.findtext('fuzzyStart')
            start = dates.findtext('start')

            if fuzzy_start:
                task.date_start = fuzzy_start
            elif start:
                task.date_start = start

            taglist = element.find('tags')

            if taglist is not None:
                for t in taglist.iter('tag'):
                    try:
                        tag_store.get(t.text)
                    except KeyError:
                        pass

            # Content
            content = element.find('content').text or ''
            content = content.replace(']]&gt;', ']]>')
            task.content = content

            self.add(task)

            log.debug('Added %s', task)


        # All tasks have been added, now we parent them
        for element in elements:
            parent_tid = element.get('id')
            subtasks = element.find('subtasks')

            for sub in subtasks.findall('sub'):
                self.parent(sub.text, parent_tid)


    def to_xml(self) -> Element:

        root = Element('Tasklist')

        for task in self.lookup.values():
            element = SubElement(root, self.XML_TAG)
            element.set('id', str(task.id))

            if task.status == Status.ACTIVE:
                element.set('status', 'Active')
            elif task.status == Status.DONE:
                element.set('status', 'Done')
            else:
                element.set('status', 'Dismissed')

            title = SubElement(element, 'title')
            title.text = task.title

            tags = SubElement(element, 'tags')

            for t in task.tags:
                tag_tag = SubElement(tags, 'tag')
                tag_tag.text = str(t.id)

            dates = SubElement(element, 'dates')

            added_date = SubElement(dates, 'added')
            added_date.text = task.date_added.isoformat()

            modified_date = SubElement(dates, 'modified')
            modified_date.text = task.date_modified.xml_str()

            done_date = SubElement(dates, 'done')
            done_date.text = task.date_closed.xml_str()

            due_date = task.due_date
            due_tag = 'fuzzyDue' if due_date.is_fuzzy() else 'due'
            due = SubElement(dates, due_tag)
            due.text = due_date.xml_str()

            start_date = task.date_start
            start_tag = 'fuzzyStart' if start_date.is_fuzzy() else 'start'
            start = SubElement(dates, start_tag)
            start.text = start_date.xml_str()

            for subtask in task.children:
                sub = SubElement(subtasks, 'sub')
                sub.text = subtask.id

            content = SubElement(element, 'content')
            text = task.content

            # Poor man's encoding.
            # CDATA's only poison is this combination of characters.
            text = text.replace(']]>', ']]&gt;')
            content.text = CDATA(text)

        return root


    def parent(self, item_id: uuid4, parent_id: uuid4) -> None:
        """Add a child to a search."""

        try:
            item = self.lookup[item_id]
        except KeyError:
            raise

        try:
            self.data.remove(item)
            self.lookup[parent_id].children.append(item)
            item.parent = self.lookup[parent_id]

        except KeyError:
            raise


    def unparent(self, item_id: uuid4, parent_id: uuid4) -> None:
        """Remove child search from a parent."""

        for child in self.lookup[parent_id].children:
            if child.id == item_id:
                child.parent = None
                self.data.append(child)
                self.lookup[parent_id].children.remove(child)
                return

        raise KeyError
