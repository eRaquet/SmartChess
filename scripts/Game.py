import chess
import Players
import Display
from queue import Queue

#Class for creating, manipulating, and playing chess games
class Game ():

    #initiation of a chess game
    def __init__(self, players, startingFEN=chess.STARTING_FEN, display=True):

        #players -> [black, white] such that players[chess.COLOR] is the corrisponding color
        self.players = players

        #set up major components
        self.whitePlayer = players[chess.WHITE]
        self.blackPlayer = players[chess.BLACK]
        self.board = chess.Board(startingFEN)
        self.boardMap = self.board.piece_map()

        #hand the game object to the players
        self.players[chess.WHITE].game = self
        self.players[chess.BLACK].game = self

        if display != None:
            self.display = Display.Display(self)

        else:
            self.display = None


    #prompt the players (either human or bot) to make a move, and perform that move
    def makeMove(self):

        self.move = self.players[self.board.turn].getMove(self.board, self.display)
        self.board.push(self.move)
        self.boardMap = self.board.piece_map()
        if self.display != None:
            self.display.displayBoard()

game = Game([Players.Human(), Players.Human()])

while True:
    if game.board.is_checkmate() == True:
        game.display.endDisplay()
        game = Game([Players.Human(), Players.Human()])
    else:
        game.makeMove()