import subprocess

import EverquestLogFile


#
# simple utility to prevent Everquest Death Loop
#
# In this case, we will define a death loop as any time a player experiences
# 'D' deaths in 'M' minutes, and no player activity during that time
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

    def process_line(self, line):
        """
        this method gets called once for each parsed line

        :param line: string with a single line from the logfile
        """
        # start with base class behavior
        super().process_line(line)

        # check for death messages
        self.check_death_message(line)

        # check for indications the player is really not AFK
        self.check_not_afk(line)

        # are we death looping?  if so, kill the process
        self.deathloop_response()

    def check_death_message(self, line: str) -> None:
        """
        check for indications the player just died

        :param line: string with a single line from the logfile
        """
        pass

    def check_not_afk(self, line: str) -> None:
        """
        check for indications the player is really not AFK

        :param line: string with a single line from the logfile
        """
        pass

    def deathloop_response(self) -> None:
        """
        are we death looping?  if so, kill the process
        """

        pass


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
    EverquestLogFile.starprint('')
    EverquestLogFile.starprint('DeathLoopVaccine - Help prevent DeathLoop disease')
    EverquestLogFile.starprint('')

    dlv = DeathLoopVaccine()
    dlv.go()

    # pid_list = get_eqgame_pid_list()
    # print(pid_list)

    # note that as soon as the main thread ends, so will the child threads
    while True:
        pass


if __name__ == '__main__':
    main()
