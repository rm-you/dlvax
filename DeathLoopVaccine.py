import re
import subprocess
from datetime import datetime

import myconfig
import EverquestLogFile


#
# simple utility to prevent Everquest Death Loop
#
# In this case, we will define a death loop as any time a player experiences
# 'x' deaths in 'y' seconds, and no player activity during that time
#
class DeathLoopVaccine(EverquestLogFile.EverquestLogFile):
    """
    the class derives from the EverquestLogFile class and relies on the base class
    for the log parsing functions.

    the class overloads the process_line() method to customize the parsing for this particular need
    """

    def __init__(self):
        """
        ctor
        """
        # parent ctor
        super().__init__()

        # list of death messages
        self.death_list = list()

        # the safety catch on the kill-gun.  Set it to True to prevent actually killing
        # the eqgame.exe process.  Used for testing.
        self.kill_safety = False

    def reset(self) -> None:
        """
        Utility function to clear the death_list and reset the kill safety
        """
        self.death_list.clear()
        self.kill_safety = False

    def process_line(self, line):
        """
        this method gets called once for each parsed line

        :param line: string with a single line from the logfile
        """
        # start with base class behavior
        super().process_line(line)

        # check for death messages
        self.check_for_death(line)

        # check for indications the player is really not AFK
        self.check_not_afk(line)

        # are we death looping?  if so, kill the process
        self.deathloop_response()

    def check_for_death(self, line: str) -> None:
        """
        check for indications the player just died, and if we find it,
        save the message for later processing

        :param line: string with a single line from the logfile
        """

        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        # does this line contain a death message
        slain_regexp = r'^You have been slain by'
        m = re.match(slain_regexp, trunc_line)
        if m:
            # add this message to the list of death messages
            self.death_list.append(line)
            EverquestLogFile.starprint(f'DeathLoopVaccine:  Death count = {len(self.death_list)}')

        # a way to test - send a tell to death_loop
        slain_regexp = r'^death_loop'
        m = re.match(slain_regexp, trunc_line)
        if m:
            # add this message to the list of death messages
            # since this is just for testing, put the safety on the kill-gun
            self.death_list.append(line)
            EverquestLogFile.starprint(f'DeathLoopVaccine:  Death count = {len(self.death_list)}')
            self.kill_safety = True

        # create a datetime object for this line, using the very capable strptime() parsing function built into the datetime module
        now = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')

        # now purge any death messages that are too old
        done = False
        while not done:
            # if the list is empty, we're done
            if len(self.death_list) == 0:
                self.reset()
                done = True
            # if the list is not empty, check if we need to purge some old entries
            else:
                oldest_line = self.death_list[0]
                oldest_time = datetime.strptime(oldest_line[0:26], '[%a %b %d %H:%M:%S %Y]')
                elapsed_seconds = now - oldest_time

                if elapsed_seconds.total_seconds() > myconfig.DEATHLOOP_SECONDS:
                    # that death message is too old, purge it
                    self.death_list.pop(0)
                    EverquestLogFile.starprint(f'DeathLoopVaccine:  Death count = {len(self.death_list)}')
                else:
                    # the oldest death message is inside the window, so we're done
                    done = True

    def check_not_afk(self, line: str) -> None:
        """
        check for indications the player is really not AFK

        :param line: string with a single line from the logfile
        """

        # check for proof of life, things that indicate the player is not actually AFK
        # todo add checks for proof of life
        afk = True

        # if they are not AFK, then go ahead and purge any death messages from the list
        if not afk:
            self.reset()

    def deathloop_response(self) -> None:
        """
        are we death looping?  if so, kill the process
        """

        # if the death_list contains more deaths than the limit, then trigger the process kill
        if len(self.death_list) >= myconfig.DEATHLOOP_DEATHS:

            EverquestLogFile.starprint('---------------------------------------------------')
            EverquestLogFile.starprint('DeathLoopVaccine - Killing all eqgame.exe processes')
            EverquestLogFile.starprint('---------------------------------------------------')

            # get the list of eqgame.exe process ID's
            pid_list = get_eqgame_pid_list()
            EverquestLogFile.starprint(f'DeathLoopVaccine:  eqgame.exe process id list = {pid_list}')
            EverquestLogFile.starprint('DeathLoopVaccine - Death Messages:')
            for line in self.death_list:
                EverquestLogFile.starprint('    ' + line)

            # kill the eqgame.exe process / processes
            if not self.kill_safety:
                pass

            # purge any death messages from the list
            self.reset()


#################################################################################################
#
# standalone functions
#

def get_eqgame_pid_list() -> list[int]:
    """
    get list of process ID's for eqgame.exe.
    returns a list of process ID's (in case multiple versions of eqgame.exe are somehow running)

    :return: list of process ID integers
    """
    pid_list = list()

    # use wmic utility to get list of processes
    # data comes back in a binary block, with individual lines separated by b'\r\r\n'
    # the output of this can be seen by entering 'wmic process list brief' at the command line
    lines = subprocess.check_output(['wmic', 'process', 'list', 'brief'])

    # split the block into individual lines
    line_list = lines.split(b'\r\r\n')

    # get each line, and then split it into components
    # 0: HandleCount
    # 1: Name
    # 2: Priority
    # 3: ProcessId
    # 4: ThreadCount
    # 5: WorkingSetSize
    for line in line_list:
        # now split each line into fields
        field_list = line.split()
        if len(field_list) == 6:
            if field_list[1] == b'eqgame.exe':
                # print(f'{str(field_list[1], "utf-8)")}, {int(field_list[3])}')
                pid_list.append(int(field_list[3]))

    return pid_list


#################################################################################################


def main():
    EverquestLogFile.starprint('-------------------------------------------------')
    EverquestLogFile.starprint('DeathLoopVaccine - Help prevent DeathLoop disease')
    EverquestLogFile.starprint('-------------------------------------------------')
    EverquestLogFile.starprint(f'Checking for '
                               f'{myconfig.DEATHLOOP_DEATHS} deaths in '
                               f'{myconfig.DEATHLOOP_SECONDS} seconds, '
                               f'with no player activity in the interim (AFK)')

    # create and start the DLV parser
    dlv = DeathLoopVaccine()
    dlv.go()

    # note that as soon as the main thread ends, so will the child threads
    while True:
        pass


if __name__ == '__main__':
    main()
