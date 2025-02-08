import chess
import pygame as pg
import sys
import time
import csv
from lib.Plot import Plot

path = sys.path[0]

#go up one directory
path = path[0 : len(path) - 8]

pieceImages = {
    'p' : pg.image.load(path + '/images/blackPawn.png'),
    'r' : pg.image.load(path + '/images/blackRook.png'),
    'n' : pg.image.load(path + '/images/blackKnight.png'),
    'b' : pg.image.load(path + '/images/blackBishop.png'),
    'q' : pg.image.load(path + '/images/blackQueen.png'),
    'k' : pg.image.load(path + '/images/blackKing.png'),
    'P' : pg.image.load(path + '/images/whitePawn.png'),
    'R' : pg.image.load(path + '/images/whiteRook.png'),
    'N' : pg.image.load(path + '/images/whiteKnight.png'),
    'B' : pg.image.load(path + '/images/whiteBishop.png'),
    'Q' : pg.image.load(path + '/images/whiteQueen.png'),
    'K' : pg.image.load(path + '/images/whiteKing.png')
}

class Display ():

    def __init__(self, data, label):

        pg.init()

        self.inputMove = None
        self.end = False

        #set up graphics
        self.surf = pg.display.set_mode((520, 520))

        self.selectedSquare = None
        self.highlightMask = []

        if data != []:
            self.plots = Plot(data, label)
            self.plots.show()
        else:
            self.plots = None

        self.displayBoard(chess.Board())

    #display bit board
    def displayBitBoard(self, bitBoard):

        #create a background color
        self.surf.fill(pg.Color(100, 75, 25))

        #for every square
        for square in range(0, 64):

            column = square % 8
            row = 7 - int((square - square % 8) / 8)
            lightDark = not bool((column + row) % 2)
            color = (60 + 160 * lightDark, 35 + 130 * lightDark, 15 + 40 * lightDark) #<- this is to create nice indication colors

            pg.draw.rect(self.surf, color, pg.Rect(20 + 60 * column, 20 + 60 * row, 60, 60))

            #for every piece type
            for piece in range(0, 12):
                
                pieceType = piece % 6 #which piece?
                pieceColor = (piece < 6) #mine or yours?

                #check to see if the piece is on the bit board (and prune this square from our search)
                if bitBoard[128 * pieceType + 64 - int(pieceColor) * 64 + square] == True:


                    self.surf.blit(pieceImages[chess.Piece(pieceType + 1, pieceColor).symbol()], pg.Rect(20 + 60 * column, 20 + 60 * row, 60, 60))

                    #once we find the piece that belongs on that square, be break from this loop
                    break

        pg.display.update()

    #display board
    def displayBoard(self, board, boardMap=None):

        if boardMap == None:
            boardMap = board.piece_map()

        self.highlightMask = []

        #create a background color
        self.surf.fill(pg.Color(100, 75, 25))

        #render each square
        for i in range(0, 64):
                
            column = i % 8
            row = 7 - int((i - i % 8) / 8)
            square = i
            lightDark = (column + row) % 2

            #highlight if the current square is a possible move for the selected piece
            try:
                highlight = board.find_move(self.selectedSquare, square) in board.legal_moves
                self.highlightMask.append(square)
            except Exception:
                highlight = False

            selected = (square == self.selectedSquare)

            #if our king is on this square and check is placed on the board
            if square in boardMap and boardMap[square].color == board.turn and boardMap[square].piece_type == chess.KING and board.is_check() == True:
                color = (100, 0, 0)

            elif highlight:
                color = (15 + 130 * lightDark, 70 + 160 * lightDark, 40 * lightDark)
            
            else:
                if selected:
                    color = (0, 0, 100)
                else:  
                    color = (60 + 160 * lightDark, 35 + 130 * lightDark, 15 + 40 * lightDark)

            #draw the square color
            pg.draw.rect(self.surf, color, pg.Rect(20 + 60 * column, 20 + 60 * row, 60, 60))

            piece = boardMap.get(i)

            #if there is a piece at this square, render it onto the board
            if piece != None:
                
                #place a piece if one exist on that square
                self.surf.blit(pieceImages[piece.symbol()], pg.Rect(20 + 60 * column, 20 + 60 * row, 60, 60))

        pg.display.update()
        self.plots.show()

    #check for human input
    def getHumanInput(self, board, boardMap=None):

        if boardMap == None:
            boardMap = board.piece_map()
            
        #get events
        events = pg.event.get()

        for event in events:

        #if button pressed...
            if event.type == pg.MOUSEBUTTONDOWN:

                pos = pg.mouse.get_pos()
                
                #if mouse is over the board
                if (pos[0] >= 20 and pos[0] <= 500) and (pos[1] >= 20 and pos[1] <= 500):

                    #shift position
                    pos = (pos[0] - 20, pos[1] - 20)

                    column = int(pos[0] / 60)
                    row = 7 - int(pos[1] / 60)
                    square = column + 8 * row

                    #...no square selected->select square
                    if self.selectedSquare == None:

                        if square in boardMap:
                            if boardMap[square].color == board.turn:
                                self.selectedSquare = square
                                self.displayBoard(board, boardMap=boardMap)
                    
                    #...square is selected
                    else:

                        if square in boardMap:
                            if boardMap[square].color == board.turn and square != self.selectedSquare:
                                self.selectedSquare = square
                                self.displayBoard(board, boardMap=boardMap)
                            
                        if square in self.highlightMask:

                            #if the move is a pawn promotion
                            if boardMap[self.selectedSquare].piece_type == chess.PAWN and (chess.square_rank(square) == 7 or chess.square_rank(square) == 0):
                                self.inputMove = chess.Move(self.selectedSquare, square, chess.QUEEN)
                            else:
                                self.inputMove = chess.Move(self.selectedSquare, square)

                            self.selectedSquare = None
                            self.displayBoard(board, boardMap=boardMap)

                        else:
                            self.selectedSquare = None
                            self.displayBoard(board, boardMap=boardMap)
    
    #play through a saved game
    def replay(self, gameNum):

        with open(path + '\\savedGames\\game_' + str(gameNum) + '.csv', 'r') as gameConfig:

            read = csv.reader(gameConfig)
            
            #extract game number from row with text (for some reason there are empty rows!)
            for row in read:
                if row != []:
                    boardFen = row[0]
                    moves = row[1:]

        gameConfig.close()

        board = chess.Board(fen=boardFen)
        moveCount = 0

        #play through the moves at the command of the users mouse pushes
        while moveCount != len(moves):

            for event in pg.event.get():

                if event.type == pg.MOUSEBUTTONDOWN:

                    board.push(chess.Move.from_uci(moves[moveCount]))
                    moveCount += 1

                    self.displayBoard(board)

        #exit once the user is finished looking at the last position
        while moveCount != 0:

            for event in pg.event.get():

                if event.type == pg.MOUSEBUTTONDOWN:

                    moveCount = 0
        
        self.endDisplay()
    
    def endDisplay(self):

        pg.quit()
    
    def clearPlots(self):

        self.plots.close()