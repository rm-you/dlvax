

#
# simple utility to prevent Everquest Death Loops
#
# parses log file, and if it detects D deaths in M minutes, and no player activity in between, it 
# will kill the eqgame.exe process
#

import EverquestLogFile

class DeathLoopVaccine(EverquestLogFile.EverquestLogFile):

    #
    # ctor
    #
    def __init__(self):

        # parent ctor
        EverquestLogFile.EverquestLogFile.__init__(self)

    def process_line(self, line):
        print('*' + line, end='')

def main():


    dlv = DeathLoopVaccine()
    dlv.begin_parsing()




if __name__ == '__main__':
    main()