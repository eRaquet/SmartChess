import chess
import pygame as pg
import sys

path = sys.path[0]

#go up one directory
path = path[0 : len(path) - 8]

pieceImages = {
    'p' : pg.image.load(path + '\\images\\blackPawn.png'),
    'r' : pg.image.load(path + '\\images\\blackRook.png'),
    'n' : pg.image.load(path + '\\images\\blackKnight.png'),
    'b' : pg.image.load(path + '\\images\\blackBishop.png'),
    'q' : pg.image.load(path + '\\images\\blackQueen.png'),
    'k' : pg.image.load(path + '\\images\\blackKing.png'),
    'P' : pg.image.load(path + '\\images\\whitePawn.png'),
    'R' : pg.image.load(path + '\\images\\whiteRook.png'),
    'N' : pg.image.load(path + '\\images\\whiteKnight.png'),
    'B' : pg.image.load(path + '\\images\\whiteBishop.png'),
    'Q' : pg.image.load(path + '\\images\\whiteQueen.png'),
    'K' : pg.image.load(path + '\\images\\whiteKing.png')
}

class Display ():

    def __init__(self, game):

        self.game = game

        pg.init()

        self.inputMove = None
        self.end = False

        self.players = (1, 1) #black and white, respectively, are being played by the display--1 is human, 0 is other

        #set up graphics
        self.surf = pg.display.set_mode((520, 520))

        self.selectedSquare = None
        self.highlightMask = []

        self.displayBoard()

    #display board
    def displayBoard(self):

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
                highlight = self.game.board.find_move(self.selectedSquare, square) in self.game.board.legal_moves
                self.highlightMask.append(square)
            except Exception:
                highlight = False

            selected = (square == self.selectedSquare)

            #if our king is on this square and check is placed on the board
            if square in self.game.boardMap and self.game.boardMap[square].color == self.game.board.turn and self.game.boardMap[square].piece_type == chess.KING and self.game.board.is_check() == True:
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

            piece = self.game.boardMap.get(i)

            #if there is a piece at this square, render it onto the board
            if piece != None:
                
                #place a piece if one exist on that square
                self.surf.blit(pieceImages[piece.symbol()], pg.Rect(20 + 60 * column, 20 + 60 * row, 60, 60))

        pg.display.update()

    #check for human input
    def getHumanInput(self):
            
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

                        if square in self.game.boardMap:
                            if self.game.boardMap[square].color == self.game.board.turn:
                                self.selectedSquare = square
                                self.displayBoard()
                    
                    #...square is selected
                    else:

                        if square in self.game.boardMap:
                            if self.game.boardMap[square].color == self.game.board.turn and square != self.selectedSquare:
                                self.selectedSquare = square
                                self.displayBoard()
                            
                        if square in self.highlightMask:

                            #if the move is a pawn promotion
                            if self.game.boardMap[self.selectedSquare].piece_type == chess.PAWN and (chess.square_rank(square) == 7 or chess.square_rank(square) == 0):
                                self.inputMove = chess.Move(self.selectedSquare, square, chess.QUEEN)
                            else:
                                self.inputMove = chess.Move(self.selectedSquare, square)

                            self.selectedSquare = None
                            self.displayBoard()

                        else:
                            self.selectedSquare = None
                            self.displayBoard()
    
    def endDisplay(self):
        pg.quit()