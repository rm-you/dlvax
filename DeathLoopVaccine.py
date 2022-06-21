import subprocess

import EverquestLogFile


# get list of process ID's for eqgame.exe
def get_eqgame_pid_list() -> list[int]:
    pid_list = list()

    # use wmic utility to get list of processes
    # data comes back in a binary block, with individual lines separated by b'\r\r\n'
    # the output of this can be seen by entering 'wmic process list brief' at the command line
    data = subprocess.check_output(['wmic', 'process', 'list', 'brief'])

    # split the block into individual lines
    data_list = data.split(b'\r\r\n')

    # get each line, and then split it into components
    # 0: HandleCount
    # 1: Name
    # 2: Priority
    # 3: ProcessId
    # 4: ThreadCount
    # 5: WorkingSetSize
    for line in data_list:
        # now split each line into fields
        field_list = line.split()
        if len(field_list) == 6:
            if field_list[1] == b'eqgame.exe':
                # print(f'{str(field_list[1], "utf-8)")}, {int(field_list[3])}')
                pid_list.append(int(field_list[3]))

    return pid_list

#
# simple utility to prevent Everquest Death Loops
#
# parses log file, and if it detects D deaths in M minutes, and no player activity in between, it 
# will kill the eqgame.exe process
#

#
# create a class for this application, that derives from the EverquestLogFile class
# overload the process_line() method to customize the application's response to parsed
# lines from the log file.
#


class DeathLoopVaccine(EverquestLogFile.EverquestLogFile):

    # ctor
    def __init__(self):
        # parent ctor
        super().__init__()

    # custom parsing logic here
    # this method gets called once for each parsed line
    def process_line(self, line):
        super().process_line(line)






def main():

    EverquestLogFile.starprint('')
    EverquestLogFile.starprint('DeathLoopVaccine - Help prevent DeathLoop disease')
    EverquestLogFile.starprint('')

    dlv = DeathLoopVaccine()
    dlv.go()

    pid_list = get_eqgame_pid_list()
    print(pid_list)

    # note that as soon as the main thread ends, so will the child threads
    while True:
        pass


if __name__ == '__main__':
    main()
