import chess
import Players
import Display
import Network
import csv
import sys
import time

path = sys.path[0]

#go up one directory
path = path[0 : len(path) - 8]

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

        self.gameList = []
        self.startingFEN = startingFEN
        self.firstTurn = self.board.turn

        if display != False:
            self.display = Display.Display(self)

        else:
            self.display = None


    #prompt the players (either human or bot) to make a move, and perform that move
    def makeMove(self):

        self.move = self.players[self.board.turn].getMove(self.board, self.display, self.boardMap)

        #reach into the bot who made the move
        self.board.push(self.move)
        self.boardMap = self.board.piece_map()

        if self.display != None:
            self.display.displayBoard()

    def saveGame(self):

        self.gameList = [self.startingFEN]

        for i in range(0, len(self.board.move_stack)):

            self.gameList.append(chess.Move.uci(self.board.move_stack[i]))

        with open(path + '\\savedGames\\config.csv') as gameConfig:

            read = csv.reader(gameConfig)
            
            #extract game number from row with text (for some reason there are empty rows!)
            for row in read:
                if row != []:
                    gameNum = row[0]

        gameConfig.close()

        with open(path + '\\savedGames\\game_' + str(gameNum) + '.csv', 'w') as gameFile:

            write = csv.writer(gameFile)
            write.writerow(self.gameList)

        gameFile.close()

        with open(path + '\\savedGames\\config.csv', 'w') as gameConfig:

            write = csv.writer(gameConfig)
            write.writerow([str(int(gameNum) + 1)])

        gameConfig.close()

    def isEnd(self):

        if self.board.is_game_over() == True or (self.board.has_insufficient_material(chess.WHITE) and self.board.has_insufficient_material(chess.BLACK)) == True:
            return True

network = Network.Model((12 * 64 + 1, 300, 20, 1))

game = Game([Players.Bot(chess.BLACK, network), Players.Bot(chess.WHITE, network)], display=False)

while True:
    if game.isEnd() != True:

        t = time.time()
        game.makeMove()
        print(time.time() - t)

    else:
        break