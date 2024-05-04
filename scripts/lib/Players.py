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
            
            display.getHumanInput(board, boardMap=boardMap)

            if display.inputMove != None:
                move = display.inputMove
                display.inputMove = None

        return move
    
class Bot ():

    def __init__(self, color, network, confidence=0.0):


        self.positions = [] #boards represented by 3D bitBoard
        self.peripherals = [] #array of peripherals (stalemate, casling)
        self.boardStack = np.ndarray((1, 8, 8, 12), np.bool_)
        
        #the index location of each piece type (aux, pawn, rook, knight, bishop, queen, king)
        self.pieceIndex = {
            chess.PAWN : 0,
            chess.KNIGHT : 1,
            chess.BISHOP : 2,
            chess.ROOK : 3,
            chess.QUEEN : 4,
            chess.KING : 5
        }

        #the index offset of each piece color (my piece, other player's piece)
        self.colorOffset = {
            color : 0,
            not color : 6
        }

        self.color = color

        self.network = network
        self.confidence = confidence

    def getMove(self, board, display, boardMap):

        self.board = board

        self.initPos(boardMap)
        
        self.legalMoves = list(board.legal_moves)
        self.boardStack = np.zeros((len(self.legalMoves), 8, 8, 12), np.bool_)
        self.peripheralStack = np.zeros((len(self.legalMoves), 5), np.bool_)

        bestMove = None #best move so far (according to the model)

        #make each move and add their bit boards to the move stack
        for i in range(0, len(self.legalMoves)):

            #get a move
            move = self.legalMoves[i]

            #generate bit board for move
            bitBoard = self.bitBoardFromMove(move)

            #generate periphals
            per = np.array([False,
                            self.board.castling_rights & chess.BB_A1,
                            self.board.castling_rights & chess.BB_A8,
                            self.board.castling_rights & chess.BB_H8,
                            self.board.castling_rights & chess.BB_H1])
            if len(self.positions) != 0:
                per[0] = (np.count_nonzero(np.all(self.positions == bitBoard, axis=(1, 2, 3))) > 1)

            #check for checkmates
            self.board.push(move)
            if self.board.is_checkmate():
                self.positions.append(bitBoard)
                self.peripherals.append(per)
                self.board.pop()
                return move
            self.board.pop()
            
            self.boardStack[i] = bitBoard
            self.peripheralStack[i] = per
        
        #once all moves have been implimented, evaluate them with the current network and get the index of the best move
        index = self.evaluate(self.boardStack, self.peripheralStack)

        bestMove = self.legalMoves[index]
        self.positions.append(self.boardStack[index])
        self.peripherals.append(self.peripheralStack[index])

        return bestMove    

    #get an updated bit board logically with information about the move (meant to speed up computation)
    def bitBoardFromMove(self, move):
        fromSquare = self.squareIndex(move.from_square)
        toSquare = self.squareIndex(move.to_square)
        pieceType = self.currentMap[move.from_square].piece_type
        movePos = self.boardPos.copy() #copy the current bit board, and then make changes to it

        #remove the fromSquare from the bit board (happens no matter what kind of move it is)
        movePos[chess.square_file(fromSquare)][chess.square_rank(fromSquare)][self.pieceIndex[pieceType] + self.colorOffset[self.color]] = False

        #if the move is not a capture
        if not (move.to_square in self.currentMap):

            #if the move is not a casle
            if not (pieceType == chess.KING and abs(toSquare - fromSquare) == 2):

                #if the move is not a promotion
                if move.promotion == None:

                    #if the move is aun pasaunt (not how you spell it!!)
                    if pieceType == chess.PAWN and (abs(toSquare - fromSquare) == 7 or abs(toSquare - fromSquare) == 9):

                        #get rid of the captured pawn
                        movePos[chess.square_file(toSquare)][chess.square_rank(toSquare) - 1][self.pieceIndex[chess.PAWN] + self.colorOffset[not self.color]] = False

                    #add the piece to the bit board in its new position
                    movePos[chess.square_file(toSquare)][chess.square_rank(toSquare)][self.pieceIndex[pieceType] + self.colorOffset[self.color]] = True

                #the move is a promotion
                else:

                    #add the promoted piece to the bit board in its position
                    movePos[chess.square_file(toSquare)][7][self.pieceIndex[move.promotion] + self.colorOffset[self.color]] = True

            #the move is a casle
            else:

                #delete rook from bit board
                if toSquare > fromSquare: 
                    movePos[7][0][self.pieceIndex[chess.ROOK] + self.colorOffset[self.color]] = False
                    #place rook next the king
                    movePos[chess.square_file(toSquare) + 1][chess.square_rank(toSquare)][self.pieceIndex[chess.ROOK] + self.colorOffset[self.color]] = True
                else:
                    movePos[0][0][self.pieceIndex[chess.ROOK] + self.colorOffset[self.color]] = False
                    #place rook next the king
                    movePos[chess.square_file(toSquare) - 1][chess.square_rank(toSquare)][self.pieceIndex[chess.ROOK] + self.colorOffset[self.color]] = True

                #place king two squares offset from origin
                movePos[chess.square_file(toSquare)][chess.square_rank(toSquare)][self.pieceIndex[chess.KING] + self.colorOffset[self.color]] = True


        #the move is a capture
        else:
            
            #remove the captured piece
            capturedPiece = self.currentMap[move.to_square].piece_type
            movePos[chess.square_file(toSquare)][chess.square_rank(toSquare)][self.pieceIndex[capturedPiece] + self.colorOffset[self.color]] = False

            if move.promotion == None:

                #add the piece to the bit board in its new position
                movePos[chess.square_file(toSquare)][chess.square_rank(toSquare)][self.pieceIndex[pieceType] + self.colorOffset[self.color]] = True

            #the move is a promotion
            else:

                #add the promoted piece to the bit board in its position
                movePos[chess.square_file(toSquare)][chess.square_rank(toSquare)][self.pieceIndex[move.promotion] + self.colorOffset[self.color]] = True

        return movePos

    #evalutate a set of board positions
    def evaluate(self, boardPositions, peripherals):

        #evaluate positions
        eval = self.network.model.predict_on_batch([boardPositions.astype(np.float64), peripherals.astype(np.float64)]).T[0]

        #if playing on maximum confidence (no exploration)
        if self.confidence == float("inf"):

            #pick the highest evaluation
            
            #pick best evaluation
            self.bestEval = eval.max()

            #get index of best evaluation
            index = list(eval).index(self.bestEval)
            return index
        
        #if not playing on maximum confidence
        else:
            
            if sum((eval - np.ones(len(eval)) * eval.mean()) != np.zeros(len(eval))):
                #create a normalized distrubtion of moves
                #raised to the power of our confidence level.
                #this will allow good moves to rise to the top of the distrobution
                #while still allowing exploration to occur.
                #the goal is to have better exploration of the model's entire state-space

                #step by step construction of distribution
                eval -= min(eval)
                eval /= sum(eval)
                eval = eval**self.confidence
                eval /= sum(eval)
                index = np.random.choice(range(0, len(self.legalMoves)), p=eval)
                return index
            else:
                return 0
    
    #create a bit board from the current board position
    def initPos(self, currentMap):

        self.boardPos = np.zeros((8, 8, 12), np.bool_)
        self.currentMap = currentMap #this map is not flipped to account for the bot's color

        for square in currentMap:

            #add piece to the bit map
            self.boardPos[chess.square_file(self.squareIndex(square))][chess.square_rank(self.squareIndex(square))][self.pieceIndex[currentMap[square].piece_type] + self.colorOffset[currentMap[square].color]] = True

    #adjust a square index by color
    def squareIndex(self, square):
        if self.color == chess.BLACK:
            return 8 * (7 - int(square / 8)) + square % 8
        else:
            return square