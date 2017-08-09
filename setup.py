#!/usr/bin/env python

from distutils.core import setup
from distutils.sysconfig import PREFIX
from distutils.command.install_data import install_data
import os
import sys

class post_install(install_data):
    def run(self):
        # Call parent
        install_data.run(self)

        if glib_compile_schemas:
            # Execute commands after copying
            os.system('glib-compile-schemas %s/share/glib-2.0/schemas' % self.install_dir)

# determine lib path depending on architecture
if (os.uname()[4].find('64') != -1 or os.uname()[4].find('s390x') != -1):
    lib_dir = 'lib64'
else:
    lib_dir = 'lib'

# optionally compile glib schemas
glib_compile_schemas = True

if "--no-glib-compile-schemas" in sys.argv:
    glib_compile_schemas = False
    sys.argv.remove("--no-glib-compile-schemas")

setup(name="rhythmbox-ampache",
      cmdclass={"install_data": post_install},
      version="0.11",
      description="A Rhythmbox plugin to stream music from an Ampache server",
      author="Rhythmbox Ampache plugin team",
      author_email="rhythmbox-ampache@googlegroups.com",
      url="http://code.google.com/p/rhythmbox-ampache",
      data_files=[
          (lib_dir+"/rhythmbox/plugins/ampache", ["ampache.plugin", "ampache.py", "AmpacheBrowser.py", "AmpacheConfigDialog.py"]),
          ("share/rhythmbox/plugins/ampache", ["ampache-prefs.ui", "ampache.ico", "ampache.png"]),
          ("share/glib-2.0/schemas", ["org.gnome.rhythmbox.plugins.ampache.gschema.xml"]),
          ],
      )
