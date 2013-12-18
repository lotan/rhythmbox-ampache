# vim: expandtab shiftwidth=8 softtabstop=8 tabstop=8

import rb
from gi.repository import GObject, Gtk, Gio, PeasGtk

class AmpacheConfigDialog(GObject.Object, PeasGtk.Configurable):
        __gtype_name__ = 'AmpacheConfigDialog'
        object = GObject.property(type=GObject.Object)

        def do_create_configure_widget(self):

                self.settings = Gio.Settings('org.gnome.rhythmbox.plugins.ampache')
                self.ui = Gtk.Builder()
                self.ui.add_from_file(rb.find_plugin_file(self, 'ampache-prefs.ui'))
                self.config_dialog = self.ui.get_object('config')

                self.url = self.ui.get_object("url_entry")
                self.url.set_text(self.settings['url'])

                self.username = self.ui.get_object("username_entry")
                self.username.set_text(self.settings['username'])

                self.password = self.ui.get_object("password_entry")
                self.password.set_visibility(False)
                self.password.set_text(self.settings['password'])

                self.url.connect('changed', self.url_changed_cb)
                self.username.connect('changed', self.username_changed_cb)
                self.password.connect('changed', self.password_changed_cb)

                return self.config_dialog

        def url_changed_cb(self, widget):
                self.settings['url'] = self.url.get_text()

        def username_changed_cb(self, widget):
                self.settings['username'] = self.username.get_text()

        def password_changed_cb(self, widget):
                self.settings['password'] = self.password.get_text()
