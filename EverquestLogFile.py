import glob
import os
import re
import threading
import time

import myconfig


#################################################################################################


#
# class to encapsulate log file operations
#
class EverquestLogFile:

    #
    # ctor
    #
    def __init__(self, char_name=myconfig.DEFAULT_CHAR_NAME):

        # instance data
        self.base_directory = myconfig.BASE_DIRECTORY
        self.logs_directory = myconfig.LOGS_DIRECTORY
        self.char_name = char_name
        self.server_name = myconfig.SERVER_NAME
        self.filename = self.build_filename(self.char_name)
        self.file = None

        self.parsing = threading.Event()
        self.parsing.clear()

        self.author = ''

        self.prevtime = time.time()
        self.heartbeat = myconfig.HEARTBEAT

        # timezone string for current computer
        self.current_tzname = time.tzname[time.daylight]

    # build the file name
    # call this anytime that the filename attributes change
    def build_filename(self, charname):
        rv = self.base_directory + self.logs_directory + 'eqlog_' + charname + '_' + self.server_name + '.txt'
        return rv

    # is the file being actively parsed
    def set_parsing(self):
        self.parsing.set()

    def clear_parsing(self):
        self.parsing.clear()

    def is_parsing(self):
        return self.parsing.is_set()

    # open the file with most recent mod time (i.e. latest)
    # returns True if a new file was opened, False otherwise
    def open_latest(self, author, seek_end=True):
        # get a list of all log files, and sort on mod time, latest at top
        mask = self.base_directory + self.logs_directory + 'eqlog_*_' + self.server_name + '.txt'
        files = glob.glob(mask)
        files.sort(key=os.path.getmtime, reverse=True)

        # foo - what if there are no files in the list?
        latest_file = files[0]

        # extract the character name from the filename
        # note that windows pathnames must usess double-backslashes in the pathname
        # note that backslashes in regular expressions are double-double-backslashes
        # this expression replaces double \\ with quadruple \\\\, as well as the filename mask asterisk to a
        # named regular expression
        charname_regexp = mask.replace('\\', '\\\\').replace('eqlog_*_', 'eqlog_(?P<charname>[\w ]+)_')
        m = re.match(charname_regexp, latest_file)
        char_name = m.group('charname')

        rv = False

        # figure out what to do
        # if we are already parsing a file, and it is the lastest file - do nothing
        if self.is_parsing() and (self.filename == latest_file):
            # do nothing
            pass

        # if we are already parsing a file, but it is not the latest file, close the old and open the latest
        elif self.is_parsing() and (self.filename != latest_file):
            # stop parsing old and open the new file
            self.close()
            rv = self.open(author, char_name, latest_file, seek_end)

        # if we aren't parsing any file, then open latest
        elif not self.is_parsing():
            rv = self.open(author, char_name, latest_file, seek_end)

        return rv

    # open the file
    # seek file position to end of file if passed parameter 'seek_end' is true
    def open(self, author, charname, filename, seek_end=True):
        try:
            self.file = open(filename, 'r', errors='ignore')
            if seek_end:
                self.file.seek(0, os.SEEK_END)

            self.author = author
            self.char_name = charname
            self.filename = filename
            self.set_parsing()
            return True
        except OSError as err:
            print("OS error: {0}".format(err))
            print('Unable to open filename: [{}]'.format(filename))
            return False

    # close the file
    def close(self):
        self.file.close()
        self.author = ''
        self.clear_parsing()

    # get the next line
    def readline(self):
        if self.is_parsing():
            return self.file.readline()
        else:
            return None
