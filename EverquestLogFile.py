import glob
import os
import re
import threading
import time

import myconfig


# allow for testing, by forcing the bot to read an old log file
TEST_ELF = False
# TEST_ELF = True


#################################################################################################


#
# class to encapsulate log file operations
#
class EverquestLogFile(threading.Thread):

    #
    # ctor
    #
    def __init__(self):

        # parent ctor
        super().__init__()

        # instance data
        self.base_directory = myconfig.BASE_DIRECTORY
        self.logs_directory = myconfig.LOGS_DIRECTORY
        self.char_name = 'Unknown'
        self.server_name = myconfig.SERVER_NAME
        self.filename = self.build_filename(self.char_name)
        self.file = None

        self.parsing = threading.Event()
        self.parsing.clear()

        self.prevtime = time.time()
        self.heartbeat = myconfig.HEARTBEAT

        # timezone string for current computer
        self.current_tzname = time.tzname[time.daylight]

        # start parsing
        self.begin_parsing()

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
    def open_latest(self, seek_end=True):
        # get a list of all log files, and sort on mod time, latest at top
        mask = self.base_directory + self.logs_directory + 'eqlog_*_' + self.server_name + '.txt'
        files = glob.glob(mask)
        files.sort(key=os.path.getmtime, reverse=True)

        # todo foo - what if there are no files in the list?
        latest_file = files[0]

        # extract the character name from the filename
        # note that windows pathnames must use double-backslashes in the pathname
        # note that backslashes in regular expressions are double-double-backslashes
        # this expression replaces double \\ with quadruple \\\\, as well as the filename mask asterisk to a
        # named regular expression
        charname_regexp = mask.replace('\\', '\\\\').replace('eqlog_*_', 'eqlog_(?P<charname>[\\w ]+)_')
        m = re.match(charname_regexp, latest_file)
        char_name = m.group('charname')

        rv = False

        # figure out what to do
        # if we are already parsing a file, and it is the latest file - do nothing
        if self.is_parsing() and (self.filename == latest_file):
            # do nothing
            pass

        # if we are already parsing a file, but it is not the latest file, close the old and open the latest
        elif self.is_parsing() and (self.filename != latest_file):
            # stop parsing old and open the new file
            self.close()
            rv = self.open(char_name, latest_file, seek_end)

        # if we aren't parsing any file, then open latest
        elif not self.is_parsing():
            rv = self.open(char_name, latest_file, seek_end)

        return rv

    # open the file
    # seek file position to end of file if passed parameter 'seek_end' is true
    def open(self, charname, filename, seek_end=True):
        try:
            self.file = open(filename, 'r', errors='ignore')
            if seek_end:
                self.file.seek(0, os.SEEK_END)

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
        self.clear_parsing()

    # get the next line
    def readline(self):
        if self.is_parsing():
            return self.file.readline()
        else:
            return None

    # call this method to kick off the parsing thread
    def begin_parsing(self):

        # already parsing?
        if self.is_parsing():
            print('Already parsing character log for: [{}]'.format(self.char_name))

        else:

            # use a back door to force the system to read a test file
            if TEST_ELF:

                # read a sample file for testing
                filename = 'test_log.txt'

                # start parsing, but in this case, start reading from the beginning of the file,
                # rather than the end (default)
                rv = self.open('Testing', filename, seek_end=False)

            # open the latest file
            else:
                # open the latest file, and kick off the parsing process
                rv = self.open_latest()

            # if the log file was successfully opened, then initiate parsing
            if rv:

                # status message
                print('Now parsing character log for: [{}]'.format(self.char_name))

                # create the background process and kick it off
                self.run()

            else:
                print('ERROR: Could not open character log file for: [{}]'.format(self.char_name))
                print('Log filename: [{}]'.format(self.filename))

    #
    # override the thread.run() method
    # this method will execute in its own thread
    #
    def run(self):

        print('----------------------------Parsing Started----------------------------')

        # process the log file lines here
        while self.is_parsing():

            # read a line
            line = self.readline()
            now = time.time()
            if line:
                self.prevtime = now

                # process this line
                self.process_line(line)

            else:

                # don't check the heartbeat if we are just testing
                if not TEST_ELF:

                    # check the heartbeat.  Has our logfile gone silent?
                    elapsed_seconds = (now - self.prevtime)

                    if elapsed_seconds > self.heartbeat:
                        print('Heartbeat over limit, elapsed seconds = {}'.format(elapsed_seconds))
                        self.prevtime = now

                        # attempt to open latest log file - returns True if a new logfile is opened
                        if self.open_latest():
                            print('Now parsing character log for: [{}]'.format(self.char_name))

                # if we didn't read a line, pause just for a 100 msec blink
                time.sleep(0.1)

        print('----------------------------Parsing Stopped----------------------------')

    #
    # virtual method, to be overridden in derived classes to do whatever specialized
    # parsing is required for this application.
    # Default behavior is to simply print() the line, with a * star at the start
    #
    def process_line(self, line):
        print('*' + line, end='')


#
# test driver
#
def main():
    elf = EverquestLogFile()


if __name__ == '__main__':
    main()
