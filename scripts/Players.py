import chess

#human chess player object
class Human ():

    #setup human player
    def __init__(self):

        self.game = None

    #get move from Human
    def getMove(self, board, display):

        move = None

        #wait until the player enters a valid move
        while move == None:
            
            display.getHumanInput()

            if display.inputMove != None:
                move = display.inputMove
                display.inputMove = None

        return move