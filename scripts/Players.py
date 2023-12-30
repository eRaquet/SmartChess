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
    def getMove(self, board, display, boardMap):

        move = None

        #wait until the player enters a valid move
        while move == None:
            
            display.getHumanInput()

            if display.inputMove != None:
                move = display.inputMove
                display.inputMove = None

        return move
    
class Bot ():

    def __init__(self, color, network, noise=0.0):

        self.auxParam = 1 #number of extra parameters given to the network other than the board (check, stalemate, etc.)

        self.positions = []
        self.boardStack = np.ndarray((1, 12*64 + self.auxParam), np.bool_)
        
        #the index location of each piece type (aux, pawn, rook, knight, bishop, queen, king)
        self.pieceIndex = {
            chess.PAWN : 0,
            chess.KNIGHT : 2 * 64,
            chess.BISHOP : 4 * 64,
            chess.ROOK : 6 * 64,
            chess.QUEEN : 8 * 64,
            chess.KING : 10 * 64
        }

        #the index offset of each piece color (my piece, other player's piece)
        self.colorOffset = {
            color : 0,
            not color : 64
        }

        self.color = color

        self.network = network
        self.noise = noise

    def getMove(self, board, display, boardMap):

        self.board = board
        self.initPos(boardMap)
        self.legalMoves = list(board.legal_moves)
        self.boardStack = np.ndarray((len(self.legalMoves), 12*64 + self.auxParam), np.bool_)

        bestMove = None #best move so far (according to the model)

        #make each move and add their bit boards to the move stack
        for i in range(0, len(self.legalMoves)):

            #generate a bit board move
            move = self.legalMoves[i]
            bitBoard = self.bitBoardFromMove(move)
            self.boardStack[i] = bitBoard
        
        #once all moves have been implimented, evaluate them with the current network and get the index of the best move
        index = self.evaluate(self.boardStack)

        bestMove = self.legalMoves[index]
        self.positions.append(self.boardStack[index])

        return bestMove
    
    #get an updated bit board logically with information about the move (meant to speed up computation)
    def bitBoardFromMove(self, move):
        fromSquare = self.squareIndex(move.from_square)
        toSquare = self.squareIndex(move.to_square)
        pieceType = self.currentMap[move.from_square].piece_type
        movePos = self.boardPos.copy() #copy the current bit board, and then make changes to it

        #remove the fromSquare from the bit board (happens no matter what kind of move it is)
        movePos[self.pieceIndex[pieceType] + self.colorOffset[self.color] + fromSquare] = False

        #if the move is not a capture
        if not (move.to_square in self.currentMap):

            #if the move is not a casle
            if not (pieceType == chess.KING and abs(toSquare - fromSquare) == 2):

                #if the move is not a promotion
                if move.promotion == None:

                    #if the move is aun pasaunt (not how you spell it!!)
                    if pieceType == chess.PAWN and (abs(toSquare - fromSquare) == 7 or abs(toSquare - fromSquare) == 9):

                        #get rid of the captured pawn
                        movePos[self.pieceIndex[chess.PAWN] + self.colorOffset[not self.color] + toSquare - 8] = False

                    #add the piece to the bit board in its new position
                    movePos[self.pieceIndex[pieceType] + self.colorOffset[self.color] + toSquare] = True

                #the move is a promotion
                else:

                    #add the promoted piece to the bit board in its position
                    movePos[self.pieceIndex[move.promotion] + self.colorOffset[self.color] + toSquare] = True

            #the move is a casle
            else:

                #delete rook from bit board
                movePos[self.pieceIndex[chess.ROOK] + self.colorOffset[self.color] + int((toSquare - fromSquare + 2)/4) * 7] = False #the 56 logic effectivally chooses which file to delete the rook from

                #place king two squares offset from origin
                movePos[self.pieceIndex[chess.KING] + self.colorOffset[self.color] + toSquare] = True

                #place rook next the king
                movePos[self.pieceIndex[chess.ROOK] + self.colorOffset[self.color] + fromSquare + int((toSquare - fromSquare)/2)] = True

        #the move is a capture
        else:
            
            #remove the captured piece
            capturedPiece = self.currentMap[move.to_square].piece_type
            movePos[self.pieceIndex[capturedPiece] + self.colorOffset[not self.color] + toSquare] = False

            if move.promotion == None:

                #add the piece to the bit board in its new position
                movePos[self.pieceIndex[pieceType] + self.colorOffset[self.color] + toSquare] = True

            #the move is a promotion
            else:

                #add the promoted piece to the bit board in its position
                movePos[self.pieceIndex[move.promotion] + self.colorOffset[self.color] + toSquare] = True

        #check for three-fold repetition
        if np.count_nonzero(np.all(self.boardStack == movePos, axis=1)) > 1:
            movePos[12 * 64] = True #toggle the three-fold repetition bit

        return movePos

    #evalutate a set of board positions
    def evaluate(self, boardPositions):

        eval = self.network.model.predict_on_batch(boardPositions).T[0] + (np.random.random(len(boardPositions)) * 2 - 1.0) * self.noise
        index = list(eval).index(eval.max())
        return index
    
    #create a bit board from the current board position
    def initPos(self, currentMap):

        self.boardPos = np.zeros(12*64 + self.auxParam, np.bool_)
        self.currentMap = currentMap #this map is not flipped to account for the bot's color

        for square in currentMap:

            #add piece to the bit map
            self.boardPos[self.pieceIndex[currentMap[square].piece_type] + self.colorOffset[currentMap[square].color] + self.squareIndex(square)] = True

    #adjust a square index by color
    def squareIndex(self, square):
        if self.color == chess.BLACK:
            return 63 - square
        else:
            return square