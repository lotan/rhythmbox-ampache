#!/usr/bin/env python

from distutils.core import setup
from distutils.sysconfig import PREFIX
from distutils.command.install_data import install_data
import os

class post_install(install_data):
    def run(self):
        # Call parent
        install_data.run(self)

        # Execute commands after copying
        os.system('glib-compile-schemas %s/share/glib-2.0/schemas' % self.install_dir)

setup(name="rhythmbox-ampache",
      cmdclass={"install_data": post_install},
      version="0.11",
      description="A Rhythmbox plugin to stream music from an Ampache server",
      author="Rhythmbox Ampache plugin team",
      author_email="rhythmbox-ampache@googlegroups.com",
      url="http://code.google.com/p/rhythmbox-ampache",
      data_files=[
          ("lib/rhythmbox/plugins/ampache", ["ampache.plugin", "ampache.py", "AmpacheBrowser.py", "AmpacheConfigDialog.py"]),
          ("share/rhythmbox/plugins/ampache", ["ampache-prefs.ui", "ampache.ico", "ampache.png"]),
          ("share/glib-2.0/schemas", ["org.gnome.rhythmbox.plugins.ampache.gschema.xml"]),
          ],
      )
