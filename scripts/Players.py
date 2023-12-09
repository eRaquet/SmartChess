import chess
import random
import numpy as np
import time

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
    
class Bot ():

    def __init__(self, color):

        self.auxParam = 1 #number of extra parameters given to the network other than the board (check, stalemate, etc.)

        self.positions = []
        self.evaluations = []
        self.boardGrid = [False] * (12*64 + self.auxParam)
        
        #the index location of each piece type (aux, pawn, rook, knight, bishop, queen, king)
        self.pieceIndex = {
            chess.PAWN : 0 + self.auxParam,
            chess.ROOK : 2 * 64 + self.auxParam,
            chess.KNIGHT : 4 * 64 + self.auxParam,
            chess.BISHOP : 6 * 64 + self.auxParam,
            chess.QUEEN : 8 * 64 + self.auxParam,
            chess.KING : 10 * 64 + self.auxParam
        }

        #the index offset of each piece color (my piece, other player's piece)
        self.colorOffset = {
            color : 0,
            not color : 64
        }

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

            self.recordPos(board, alpha)

            #undo move
            self.board.pop()
        
        return bestMove

    #evalutate the current state of the board
    def evalutate(self):
        return (random.random() - 0.5) * 2
    
    def recordPos(self, board, alpha):

        self.boardGrid = [False] * (12*64 + self.auxParam)

        self.moveBoardMap = board.piece_map()

        for square in self.moveBoardMap:

            #flip the bit at the location of each piece in the boardGrid scheme
            self.boardGrid[self.pieceIndex[self.moveBoardMap[square].piece_type] + self.colorOffset[self.moveBoardMap[square].color] + square] = True

        #insert auxilary parameters
        self.boardGrid[0] = (self.positions.count(self.boardGrid) > 2)

        self.positions.append(self.boardGrid)
        self.evaluations.append(alpha)