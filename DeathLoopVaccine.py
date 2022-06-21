import EverquestLogFile

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

    # note that as soon as the main thread ends, so will the child threads
    while True:
        pass


if __name__ == '__main__':
    main()
