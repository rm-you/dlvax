import re
import os
import signal
import subprocess
from datetime import datetime

import myconfig
import EverquestLogFile


#
# simple utility to prevent Everquest Death Loop
#
# The utility functions by parsing the current (most recent) Everquest log file, and if it detects
# Death Loop symptoms, it will respond by initiating a system process kill of all "eqgame.exe"
# processes (there should usually only be one).
#
# We will define a death loop as any time a player experiences X deaths in Y seconds, and no player
# activity during that time.  The values for X and Y are configurable, via the myconfig.py file.
#
# For testing purposes, there is a back door feature, controlled by sending a tell to the following
# non-existent player:
#
#   death_loop:     Simulates a player death.
#
#                   Note however that this also sets a flag that disarms the conceptual
#                   "process-killer gun", which will allow every bit of the code to
#                   execute and be tested, but will stop short of actually killing any
#                   process
#
#                   The "process-killer gun" will then be armed again after the simulated
#                   player deaths trigger the simulated process kill, or after any simulated
#                   player death events "scroll off" the death loop monitoring window.
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
        self.kill_armed = True

    def reset(self) -> None:
        """
        Utility function to clear the death_list and reset the kill safety
        """
        self.death_list.clear()
        self.kill_armed = True

    def process_line(self, line):
        """
        this method gets called once for each parsed line

        :param line: string with a single line from the logfile
        """
        # start with base class behavior
        # check for death messages
        # check for indications the player is really not AFK
        # are we death looping?  if so, kill the process
        super().process_line(line)
        self.check_for_death(line)
        self.check_not_afk(line)
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
        slain_regexp = r'^You have been slain'
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
            self.kill_armed = False

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
        afk = True

        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        # does this line contain a proof of life - casting
        regexp = r'^You begin casting'
        m = re.match(regexp, trunc_line)
        if m:
            # player is not AFK
            afk = False
            EverquestLogFile.starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

        # does this line contain a proof of life - tells
        regexp = r'^You told'
        m = re.match(regexp, trunc_line)
        if m:
            # player is not AFK
            afk = False
            EverquestLogFile.starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

        # does this line contain a proof of life - melee
        regexp = r'^You( try to)? (hit|slash|pierce|crush|claw|bite|sting|maul|gore|punch|kick|backstab|bash)'
        m = re.match(regexp, trunc_line)
        if m:
            # player is not AFK
            afk = False
            EverquestLogFile.starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

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
            EverquestLogFile.starprint('DeathLoopVaccine has detected deathloop symptoms:')
            EverquestLogFile.starprint(f'    {myconfig.DEATHLOOP_DEATHS} deaths in less than '
                                       f'{myconfig.DEATHLOOP_SECONDS} seconds, with no player activity')

            # get the list of eqgame.exe process ID's
            pid_list = get_eqgame_pid_list()
            EverquestLogFile.starprint('Death Messages:')
            for line in self.death_list:
                EverquestLogFile.starprint('    ' + line)
            EverquestLogFile.starprint(f'eqgame.exe process id list = {pid_list}')

            # kill the eqgame.exe process / processes
            for pid in pid_list:
                EverquestLogFile.starprint(f'Killing process [{pid}]')

                # for testing the actual kill process, uncomment the following line
                # self.kill_armed = True
                if self.kill_armed:
                    os.kill(pid, signal.SIGKILL)

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
