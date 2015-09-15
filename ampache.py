# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
# vim: expandtab shiftwidth=8 softtabstop=8 tabstop=8
#
# (c) 2010
#       envyseapets@gmail.com
#       grindlay@gmail.com
#       langdalepl@gmail.com
#       massimo.mund@googlemail.com
#       bethebunny@gmail.com,
# 2012-2015 lotan_rm@gmx.de
#
# This file is part of the Rhythmbox Ampache plugin.
#
# The Rhythmbox Ampache plugin is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# The Rhythmbox Ampache plugin is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the Rhythmbox Ampache plugin.  If not, see
# <http://www.gnu.org/licenses/>.

import rb
from gi.repository import RB
from gi.repository import GObject, Peas, Gtk, Gio, GdkPixbuf

from AmpacheConfigDialog import AmpacheConfigDialog
from AmpacheBrowser import AmpacheBrowser

class AmpacheEntryType(RB.RhythmDBEntryType):
        def __init__(self):
                RB.RhythmDBEntryType.__init__(
                                self,
                                name='AmpacheEntryType',
                                save_to_disk=False)

        def can_sync_metadata(self, entry):
                return True

        def sync_metadata(self, entry, changes):
                return


class Ampache(GObject.Object, Peas.Activatable):
        __gtype_name__ = 'AmpachePlugin'
        object = GObject.property(type=GObject.Object)

        def do_activate(self):
                shell = self.object
                db = shell.props.db

                # load icon
                theme = Gtk.IconTheme.get_default()
                what, width, height = Gtk.icon_size_lookup(Gtk.IconSize.LARGE_TOOLBAR)
                icon = GdkPixbuf.Pixbuf.new_from_file_at_size(rb.find_plugin_file(self, 'ampache.ico'), width, height)

                # register AmpacheEntryType
                self.__entry_type = AmpacheEntryType()
                db.register_entry_type(self.__entry_type)

                # fetch plugin settings
                settings = Gio.Settings("org.gnome.rhythmbox.plugins.ampache")

                menu = Gio.Menu()
                menu.append('Refetch Ampache Library', 'app.refetch-ampache')

                # create AmpacheBrowser source
                self.__source = GObject.new(
                        AmpacheBrowser,
                        shell=shell,
                        entry_type=self.__entry_type,
                        icon=icon,
                        plugin=self,
                        settings=settings.get_child("source"),
                        toolbar_menu=menu,
                        name=_("Ampache")
                )
                self.__first = 1

                # assign AmpacheEntryType to AmpacheBrowser source
                shell.register_entry_type_for_source(
                        self.__source,
                        self.__entry_type)


                # insert AmpacheBrowser source into Shared group
                shell.append_display_page(
                        self.__source,
                        RB.DisplayPageGroup.get_by_id("shared"))

        def do_deactivate(self):
                # destroy AmpacheBrowser source
                self.__source.delete_thyself()
                self.__source = None

                # destroy entry type
                self.__entry_type = None
