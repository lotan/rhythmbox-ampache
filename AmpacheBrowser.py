# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t;
# -*- vim: expandtab shiftwidth=8 softtabstop=8 tabstop=8
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

from gi.repository import RB
from gi.repository import GObject, Gtk, Gio, GLib

import time
from time import mktime
from datetime import datetime
import re
import hashlib
import os
import os.path
import sys
import collections

import xml.sax, xml.sax.handler

class HandshakeHandler(xml.sax.handler.ContentHandler):
        def __init__(self, handshake):
                xml.sax.handler.ContentHandler.__init__(self)
                self.__handshake = handshake

        def startElement(self, name, attrs):
                self.__text = ''

        def endElement(self, name):
                self.__handshake[name] = self.__text

        def characters(self, content):
                self.__text = self.__text + content

class PlaylistsHandler(xml.sax.handler.ContentHandler):
        def __init__(self, playlists, user):
                xml.sax.handler.ContentHandler.__init__(self)
                self.__playlists = playlists
                self.__user = user

        def startElement(self, name, attrs):
                if name == 'playlist' and attrs['id'].isdigit():
                        self.__id = int(attrs['id'])
                self.__text = ''

        def endElement(self, name):
                if name == 'playlist':
                        # only private with your user name or public
                        # playlists should be considered
                        if self.__owner == self.__user or \
                                self.__type == 'public':
                                self.__playlists.append([
                                        self.__id,
                                        self.__name,
                                        self.__items])
                elif name == 'name':
                        self.__name = self.__text
                elif name == 'items' and self.__text.isdigit():
                        self.__items = int(self.__text)
                elif name == 'owner':
                        self.__owner = self.__text
                elif name == 'type':
                        self.__type = self.__text
                else:
                        self.__null = self.__text

        def characters(self, content):
                self.__text = self.__text + content

class SongsHandler(xml.sax.handler.ContentHandler):
        def __init__(self, is_playlist, source, db, entry_type, albumart, auth, entries):
                xml.sax.handler.ContentHandler.__init__(self)
                self.__is_playlist = is_playlist
                self.__source = source
                self.__db = db
                self.__entry_type = entry_type
                self.__albumart = albumart
                self.__auth = auth
                self.__entries = entries
                self.__default()
                self.__re_auth = re.compile('\\b(auth|ssid)=[a-fA-F0-9]*')

        def startElement(self, name, attrs):
                if name == 'song':
                        self.__id = attrs['id']
                self.__text = ''

        def endElement(self, name):
                if self.__text:
                        if name == 'song':
                                try:
                                        if self.__is_playlist:
                                                self.__source.add_location(self.__url, -1)
                                        else:
                                                # add the track to the database if it doesn't exist
                                                entry = self.__db.entry_lookup_by_location(self.__url)
                                                if entry == None:
                                                        entry = RB.RhythmDBEntry.new(self.__db, self.__entry_type, self.__url)
                                                        self.__entries.append(entry)

                                                        if self.__artist != '':
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.ARTIST, self.__artist)
                                                        if self.__album != '':
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.ALBUM, self.__album)
                                                        if self.__title != '':
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.TITLE, self.__title)
                                                        if self.__tag != '':
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.GENRE, self.__tag)
                                                        if self.__track != -1:
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.TRACK_NUMBER, self.__track)
                                                        if self.__year:
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.DATE, self.__year)
                                                        if self.__time != -1:
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.DURATION, self.__time)
                                                        if self.__size != -1:
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.FILE_SIZE, self.__size)
                                                        if self.__rating != -1:
                                                                self.__db.entry_set(entry, RB.RhythmDBPropType.RATING, self.__rating)
                                                        self.__db.commit()

                                                        if self.__art != '':
                                                                self.__albumart[self.__artist + self.__album] = self.__art

                                except Exception as e: # This happens on duplicate uris being added
                                        sys.excepthook(*sys.exc_info())
                                        print("Couldn't add %s - %s" % (self.__artist, self.__title), e)

                                self.__default()

                        elif name == 'url':
                                if self.__auth: # replace ssid string with new auth string
                                        self.__text = re.sub(self.__re_auth, r'\1='+self.__auth, self.__text);
                                self.__url = self.__text
                        elif name == 'artist':
                                self.__artist = self.__text
                        elif name == 'album':
                                self.__album = self.__text
                        elif name == 'title':
                                self.__title = self.__text
                        elif name == 'tag':
                                self.__tag = self.__text
                        elif name == 'track' and self.__text.isdigit():
                                self.__track = int(self.__text)
                        elif name == 'year' and self.__text.isdigit():
                                if (GLib.Date.valid_year(int(self.__text))):
                                        self.__year = GLib.Date.new_dmy(1, 1, int(self.__text)).get_julian()
                        elif name == 'time' and self.__text.isdigit():
                                self.__time = int(self.__text)
                        elif name == 'size' and self.__text.isdigit():
                                self.__size = int(self.__text)
                        elif name == 'rating' and self.__text.isdigit():
                                self.__rating = int(self.__text)
                        elif name == 'art':
                                if self.__auth: # replace auth string with new auth string
                                        self.__text = re.sub(self.__re_auth, 'auth='+self.__auth, self.__text);
                                self.__art = self.__text
                        else:
                                self.__null = self.__text

        def characters(self, content):
                self.__text = self.__text + content

        def __default(self):
                self.__id = -1
                self.__url = ''
                self.__artist = ''
                self.__album = ''
                self.__title = ''
                self.__tag = ''
                self.__track = -1
                self.__year = -1
                self.__time = -1
                self.__size = -1
                self.__rating = -1
                self.__art = ''
 
class AmpachePlaylist(RB.StaticPlaylistSource):
        def __init__(self, **kwargs):
                super(AmpachePlaylist, self).__init__(kwargs)

GObject.type_register(AmpachePlaylist)

class AmpacheBrowser(RB.BrowserSource):

        def __init__(self, **kwargs):
                super(AmpacheBrowser, self).__init__(kwargs)

                self.__limit = 5000

                self.__songs_cache = '_songs'
                self.__cache_directory = os.path.join(
                        RB.user_cache_dir(),
                        'ampache')
                self.__songs_cache_filename = os.path.join(
                        self.__cache_directory,
                        ''.join([self.__songs_cache, '.xml']))
                self.__settings = Gio.Settings('org.gnome.rhythmbox.plugins.ampache')
                self.__albumart = {}
                self.__playlists = collections.deque(
                        [[0, self.__songs_cache]])
                self.__caches = collections.deque()
                self.__playlist_sources = []
                self.__entries = []

                self.__text = None
                self.__progress_text = None
                self.__progress = 1

                self.__activated = False

                # add action RefetchAmpache and assign callback refetch_ampache
                app = Gio.Application.get_default()
                action = Gio.SimpleAction(name='refetch-ampache')
                action.connect('activate', self.refetch_ampache)
                app.add_action(action)

        def update(self, force_download):

                ### download songs from Ampache server

                def download_songs(uri, items, is_playlist, source, cache_filename, playlist_name):

                        def cache_saved_cb(stream, result, data):
                                try:
                                        size = stream.write_bytes_finish(result)
                                except Exception as e:
                                        print("error writing file: %s" % (self.__songs_cache_filename))
                                        sys.excepthook(*sys.exc_info())

                                # close stream
                                stream.close(Gio.Cancellable())

                                # change modification time to newest time
                                newest_time = int(mktime(self.__handshake_newest.timetuple()))
                                os.utime(cache_filename, (newest_time, newest_time))

                        def open_append_cb(file, result, data):
                                try:
                                        stream = file.append_to_finish(result)
                                except Exception as e:
                                        print("error opening file for writing %s" % (cache_filename))
                                        sys.excepthook(*sys.exc_info())

                                stream.write_bytes_async(
                                        data,
                                        GLib.PRIORITY_DEFAULT,
                                        Gio.Cancellable(),
                                        cache_saved_cb,
                                        None)
                                print("write to cache file: %s" % (cache_filename))

                        def songs_downloaded_cb(file, result, data):
                                try:
                                        (ok, contents, etag) = file.load_contents_finish(result)
                                except Exception as e:
                                        edlg = Gtk.MessageDialog(
                                                None,
                                                0,
                                                Gtk.MessageType.ERROR,
                                                Gtk.ButtonsType.OK,
                                                _('Songs response: %s') % e)
                                        edlg.run()
                                        edlg.destroy()
                                        self.__activated = False
                                        return

                                new_offset = data[0] + self.__limit

                                # show progress
                                self.__progress = float(new_offset) / float(items)
                                self.notify_status_changed()

                                # instantiate songs parser and parse XML
                                parser = xml.sax.make_parser()
                                parser.setContentHandler(SongsHandler(
                                        is_playlist,
                                        source,
                                        self.__db,
                                        self.__entry_type,
                                        self.__albumart,
                                        self.__handshake_auth,
                                        self.__entries))

                                print("parse chunk %s[%d]..." % (playlist_name, data[0]))
                                try:
                                        parser.feed(contents)
                                except xml.sax.SAXParseException as e:
                                        print("error parsing songs: %s: %s" %
                                                (e, contents.decode('utf-8').split("\n")[e.getLineNumber()]))

                                # get next chunk of move on to next playlist
                                if new_offset < items:
                                        # download subsequent chunk of songs
                                        download_songs_chunk(new_offset, data[1])
                                else:
                                        # last chunk downloaded
                                        # change progress to 100%
                                        self.__text = ''
                                        self.__progress = 1
                                        self.notify_status_changed()

                                        # process next playlist
                                        download_iterate()

                                # remove enveloping <?xml> and <root> tags
                                # as needed to regenerate one full .xml
                                lines = contents.decode('utf-8').splitlines(True)
                                if data[0] > 0:
                                        del lines[:2]
                                if new_offset < items:
                                        del lines[-2:]

                                # append to cache file
                                print("write chunk %s[%d] to file..." % (playlist_name, data[0]))
                                data[1].append_to_async(
                                        Gio.FileCreateFlags.NONE,
                                        GLib.PRIORITY_DEFAULT,
                                        Gio.Cancellable(),
                                        open_append_cb,
                                        GLib.Bytes.new(''.join(lines).encode('utf-8')))

                        def download_songs_chunk(offset, cache_file):
                                ampache_server_uri = ''.join([uri,
                                        '&offset=%s&limit=%s' % (offset, self.__limit)])
                                ampache_server_file = Gio.file_new_for_uri(ampache_server_uri)
                                ampache_server_file.load_contents_async(
                                        Gio.Cancellable(),
                                        songs_downloaded_cb,
                                        (offset, cache_file))
                                print("download %s[%d]: %s" %
                                        (playlist_name, offset, ampache_server_uri))

                        self.__text = 'Download %s from Ampache server...' % (playlist_name)
                        self.__progress = 0
                        self.notify_status_changed()

                        cache_file = Gio.file_new_for_path(cache_filename)

#                        cache_file = open(cache_filename, 'wt', encoding='utf-8')

                        # download first chunk of songs
                        download_songs_chunk(0, cache_file)

                def download_iterate():
                        try:
                                if len(self.__playlists) > 0:
                                        playlist = self.__playlists.popleft()
                                        print('process playlist: %s' % playlist[1])
                                        if playlist[0] == 0:
                                                download_songs(
                                                        '%s/server/xml.server.php?action=songs&auth=%s' %
                                                                (self.__settings['url'],
                                                                self.__handshake_auth),
                                                        self.__handshake_songs,
                                                        False,
                                                        self,
                                                        self.__songs_cache_filename,
                                                        playlist[1])
                                        else:
                                                # create AmpachePlaylist source
                                                playlist_source = GObject.new(
                                                        AmpachePlaylist,
                                                        is_local=False,
                                                        shell=self.__shell,
                                                        entry_type=self.__entry_type,
                                                        name=_(playlist[1])
                                                )
                                                self.__playlist_sources.append(playlist_source)

                                                # insert AmpachePlaylist source into AmpacheBrowser source
                                                self.__shell.append_display_page(playlist_source, self)

                                                download_songs(
                                                        '%s/server/xml.server.php?action=playlist_songs&filter=%d&auth=%s' % \
                                                                (self.__settings['url'],
                                                                playlist[0],
                                                                self.__handshake_auth),
                                                        playlist[2],
                                                        True,
                                                        playlist_source,
                                                        os.path.join(
                                                                self.__cache_directory,
                                                                ''.join([playlist[1], '.xml'])),
                                                        playlist[1])

                                else:
                                        print('no more playlists to process, refilter display page model')
                                        self.__shell.props.display_page_model.refilter()

                        except Exception as e:
                                print('Exception: %s' % e)
                                return


                def playlists_cb(file, result, param):
                        try:
                                (ok, contents, etag) = file.load_contents_finish(result)
                        except Exception as e:
                                edlg = Gtk.MessageDialog(
                                        None,
                                        0,
                                        Gtk.MessageType.ERROR,
                                        Gtk.ButtonsType.OK,
                                        _('Playlists response: %s') % e)
                                edlg.run()
                                edlg.destroy()
                                self.__activated = False
                                return

                        if len(contents) <= 0:
                                edlg = Gtk.MessageDialog(
                                        None,
                                        0,
                                        Gtk.MessageType.ERROR,
                                        Gtk.ButtonsType.OK,
                                        _("Playlists response size: 0\nCheck ampache server logs for cause."))
                                edlg.run()
                                edlg.destroy()
                                self.__activated = False

                                self.__text = ''
                                self.notify_status_changed()
                                return

                        # instantiate playlists parser
                        parser = xml.sax.make_parser()
                        parser.setContentHandler(PlaylistsHandler(
                                self.__playlists,
                                self.__settings['username']))

                        try:
                                parser.feed(contents)
                        except xml.sax.SAXParseException as e:
                                print("error parsing playlists: %s" % e)

                        download_iterate()

                ### load songs from cache

                def load_songs(filename, is_playlist, source):
                        def songs_loaded_cb(file, result, data):
                                try:
                                        (ok, contents, etag) = file.load_contents_finish(result)
                                except Exception as e:
                                        RB.error_dialog(
                                                title=_("Unable to load songs"),
                                                message=_("Rhythmbox could not load the Ampache songs."))
                                        return

                                try:
                                        # instantiate songs parser
                                        parser = xml.sax.make_parser()
                                        parser.setContentHandler(
                                                SongsHandler(
                                                        is_playlist,
                                                        source,
                                                        self.__db,
                                                        self.__entry_type,
                                                        self.__albumart,
                                                        self.__handshake_auth,
                                                        self.__entries))

                                        parser.feed(contents)
                                except xml.sax.SAXParseException as e:
                                        print("error parsing songs: %s" % e)

                                self.__text = ''
                                self.__progress = 1
                                self.notify_status_changed()

                                # load next cache
                                load_iterate()

                        self.__text = 'Load from cache "%s"...' % filename
                        self.__progress = 0
                        self.notify_status_changed()

                        cache_file = Gio.file_new_for_path(filename)
                        cache_file.load_contents_async(
                                Gio.Cancellable(),
                                songs_loaded_cb,
                                None)

                def load_iterate():
                        try:
                                cache = self.__caches.popleft()

                                print('process playlist: %s' % cache)

                                if cache == self.__songs_cache:
                                        load_songs(
                                                self.__songs_cache_filename,
                                                False,
                                                self)
                                else:
                                        # create AmpachePlaylist source
                                        playlist_source = GObject.new(
                                                AmpachePlaylist,
                                                is_local=False,
                                                shell=self.__shell,
                                                entry_type=self.__entry_type,
                                                name=_(cache)
                                        )
                                        self.__playlist_sources.append(playlist_source)

                                        # insert AmpachePlaylist source into AmpacheBrowser source
                                        self.__shell.append_display_page(playlist_source, self)

                                        load_songs(
                                                os.path.join(
                                                        self.__cache_directory,
                                                        ''.join([cache, '.xml'])),
                                                True,
                                                playlist_source)

                        except Exception as e:
                                print('no more playlists to process, refilter display page model')
                                self.__shell.props.display_page_model.refilter()
                                return

                def enumerate_cache_files():
                        for filename in os.listdir(
                                os.path.join(RB.user_cache_dir(), 'ampache')):
                                name = os.path.splitext(filename)[0]
                                if name == self.__songs_cache:
                                        self.__caches.appendleft(name)
                                else:
                                        self.__caches.append(name)

                        print('caches: %s' % self.__caches)

                        # start processing first cache
                        load_iterate()

                def handshake_cb(file, result, parser):
                        try:
                                (ok, contents, etag) = file.load_contents_finish(result)
                        except Exception as e:
                                edlg = Gtk.MessageDialog(
                                        None,
                                        0,
                                        Gtk.MessageType.ERROR,
                                        Gtk.ButtonsType.OK,
                                        _('Handshake response: %s') % e)
                                edlg.run()
                                edlg.destroy()
                                self.__activated = False
                                return

                        if len(contents) <= 0:
                                edlg = Gtk.MessageDialog(
                                        None,
                                        0,
                                        Gtk.MessageType.ERROR,
                                        Gtk.ButtonsType.OK,
                                        _("Handshake response size: 0\nCheck ampache server logs for cause."))
                                edlg.run()
                                edlg.destroy()
                                self.__activated = False

                                self.__text = ''
                                self.notify_status_changed()
                                return

                        try:
                                parser.feed(contents)
                        except xml.sax.SAXParseException as e:
                                print("error parsing handshake: %s" % e)

                        # convert handshake update time into datetime
                        handshake_update = datetime.strptime(
                                handshake['update'][0:18],
                                '%Y-%m-%dT%H:%M:%S')
                        self.__handshake_newest = handshake_update
                        handshake_add = datetime.strptime(
                                handshake['add'][0:18],
                                '%Y-%m-%dT%H:%M:%S')
                        if handshake_add > self.__handshake_newest:
                                self.__handshake_newest = handshake_add
                        handshake_clean = datetime.strptime(
                                handshake['clean'][0:18],
                                '%Y-%m-%dT%H:%M:%S')
                        if handshake_clean > self.__handshake_newest:
                                self.__handshake_newest = handshake_clean

                        self.__handshake_auth = handshake['auth']
                        self.__handshake_songs = int(handshake['songs'])

                        # cache file mtime >= handshake newest time: load cached
                        if not force_download and \
                                os.path.exists(self.__songs_cache_filename) and \
                                datetime.fromtimestamp(os.path.getmtime(
                                self.__songs_cache_filename)) >= \
                                self.__handshake_newest:
                                enumerate_cache_files()
                        else:
                                # delete all cache files
                                for filename in os.listdir(self.__cache_directory):
                                        abs_filename = os.path.join(
                                                self.__cache_directory,
                                                filename)
                                        try:
                                                if os.path.isfile(abs_filename):
                                                        print("remove cache file: %s" % abs_filename)
                                                        os.unlink(abs_filename)
                                        except Exception as e:
                                                print(e)

                                # download playlists
                                ampache_server_uri = \
                                        '%s/server/xml.server.php?action=playlists&auth=%s' % \
                                        (self.__settings['url'],
                                        self.__handshake_auth)
                                ampache_server_file = \
                                        Gio.file_new_for_uri(ampache_server_uri)
                                ampache_server_file.load_contents_async(
                                        Gio.Cancellable(),
                                        playlists_cb,
                                        None)
                                print("downloading playlists: %s" % (ampache_server_uri))

                # check for errors
                if not self.__settings['url']:
                        edlg = Gtk.MessageDialog(
                                None,
                                0,
                                Gtk.MessageType.ERROR,
                                Gtk.ButtonsType.OK,
                                _('URL missing'))
                        edlg.run()
                        edlg.destroy()
                        self.__activated = False
                        return

                if not self.__settings['password']:
                        edlg = Gtk.MessageDialog(
                                None,
                                0,
                                Gtk.MessageType.ERROR,
                                Gtk.ButtonsType.OK,
                                _('Password missing'))
                        edlg.run()
                        edlg.destroy()
                        self.__activated = False
                        return

                self.__text = 'Update songs...'
                self.notify_status_changed()

                handshake = {}

                # instantiate handshake parser
                parser = xml.sax.make_parser()
                parser.setContentHandler(HandshakeHandler(handshake))

                # build handshake url
                if self.__settings['username'] != '':
                        # username/password provided
                        timestamp = int(time.time())
                        password = hashlib.sha256(self.__settings['password'].encode('utf-8')).hexdigest()
                        authkey = hashlib.sha256((str(timestamp) + password).encode('utf-8')).hexdigest()

                        ampache_server_uri = \
                                '%s/server/xml.server.php?action=handshake&auth=%s&timestamp=%s&user=%s&version=350001' % \
                                (self.__settings['url'],
                                authkey,
                                timestamp,
                                self.__settings['username'])
                else:
                        # api key provided
                        ampache_server_uri = \
                                '%s/server/xml.server.php?action=handshake&auth=%s&version=350001' % \
                                (self.__settings['url'],
                                self.__settings['password'])


                # execute handshake
                ampache_server_file = Gio.file_new_for_uri(ampache_server_uri)
                ampache_server_file.load_contents_async(
                        Gio.Cancellable(),
                        handshake_cb,
                        parser)
                print("downloading handshake: %s" % (ampache_server_uri))

        # Source is activated
        def do_activate(self):
                # activate source if inactive
                if not self.__activated:
                        self.__activated = True

                        self.__shell = self.props.shell
                        self.__db = self.__shell.props.db
                        self.__entry_type = self.props.entry_type

                        # connect playing-song-changed signal
                        self.__art_store = RB.ExtDB(name="album-art")
                        self.__art_request = self.__art_store.connect("request", self.__album_art_requested)

                        # create cache directory if it doesn't exist
                        cache_path = os.path.dirname(self.__songs_cache_filename)
                        if not os.path.exists(cache_path):
                                os.mkdir(cache_path, 0o700)

                        self.update(False)

        # Shortcut for single click
        def do_selected(self):
                self.do_activate()

        def __album_art_requested(self, store, key, last_time):
                artist = key.get_field('artist')
                album = key.get_field('album')
                uri = self.__albumart[artist + album]
                print('album art uri: %s' % uri)
                if uri:
                        storekey = RB.ExtDBKey.create_storage('album', album)
                        storekey.add_field('artist', artist)
                        store.store_uri(storekey, RB.ExtDBSourceType.SEARCH, uri)

        def do_get_status(self, status, progress_text, progress):
                return (self.__text, self.__progress_text, self.__progress)

        def clean_db(self):
                # remove playlists
                for playlist_source in self.__playlist_sources:
                        # delete Playlist source
                        playlist_source.delete_thyself()
                        playlist_source = None

                self.__db.entry_delete_by_type(self.__entry_type)
                self.__db.commit()
                # self.__entries should be deleted, but here it's too soon, now it just grows on each update

        def refetch_ampache(self, parameter, user_data):
                self.clean_db()
                self.update(True)

        def do_delete_thyself(self):

                # delete source if active
                if self.__activated:
                        self.__activated = False

                        # disconnect from art store
                        self.__art_store.disconnect(self.__art_request)
                        self.__art_store = None

                        # remove all AmpacheEntryTypes from database
                        self.clean_db()

                RB.BrowserSource.do_delete_thyself(self)

GObject.type_register(AmpacheBrowser)
