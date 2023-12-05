import chess
import random

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
    
class bot ():

    def __init__(self):

        pass

    def getMove(self, board, display):

        self.board = board
        self.legalMoves = list(board.legal_moves)

        alpha = -1 #best evaluation so far
        bestMove = None #best move so far (according to the model)

        #make each move and evaluate each to determine which is the best
        for i in range(0, len(self.legalMoves)):

            #try the move
            move = self.legalMoves[i]
            self.board.push(move)

            #evaluate the board position
            evaluation = self.evalutate()

            #set the new best move
            if evaluation > alpha:
                alpha = evaluation
                bestMove = move

            #undo move
            self.board.pop()
        
        return bestMove

    #evalutate the current state of the board
    def evalutate(self):
        return (random.random() - 0.5) * 2