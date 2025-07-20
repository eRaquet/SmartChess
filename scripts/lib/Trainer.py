import lib.Game as Game
import lib.Network as Network
import lib.Players as Players
import lib.Display as Display
import time
import chess
import keras
import random
import numpy as np
import sys

path = sys.path[0]

#go up one directory
path = path[0 : len(path) - 8]

#class for training the model

#the training breakdown (with apporpriate iterators at each stage):

#Trainer -- trainSession() -> trainEpoch() -> playBot() -> playGame()

class Trainer ():

    def __init__(self, networkOffset=0, startConfidence=7.0, opponentNum=9, saveCount=6):

        self.confidence = startConfidence
        self.opponentNum = opponentNum
        self.saveCount = saveCount

        self.currentNetwork = Network.Model(offset=networkOffset)

        self.testPos = np.load(path + '/testPositions/testPositions.npy')
        self.testEval = np.load(path + '/testPositions/testEvaluations.npy')

        # training parameters
        self.nominalWinGain = 0.05
        self.blunderCatcherGain = 0.1

    #train an entire session
    def trainSession(self, epochs, gameNum, splitFraction = 0.5):

        self.epochCount = 0
        self.broadGameCount = int(splitFraction * gameNum) #the number of games we play agianst all the bots together
        self.narrowGameCount = gameNum - self.broadGameCount #the number of games we play against the victor bots

        #train each epoch of games
        while self.epochCount < epochs:

            #count how many games we played that resulted in a victory
            self.games = 0
            
            self.trainEpoch()

            self.epochCount += 1

            #if we are due to update the network
            if self.epochCount % self.saveCount == 0:
                #save the current network
                self.currentNetwork.saveModel()

        #if we haven't just saved a network
        if self.epochCount % self.saveCount != 0:
            #save the current network
            self.currentNetwork.saveModel()


    #train one epoch of games (and create one new model)
    def trainEpoch(self):

        self.boardTrainData = np.ndarray((0, 8, 8, 12))
        self.periTrainData = np.ndarray((0, 5))
        self.outputTrainData = np.ndarray(0)

        #an array that keeps track of how many wins the current model has had against other models
        #this is to be compared with self.gamesPerBot
        self.winsPerBot = np.zeros(self.opponentNum, int)

        #an array that keeps track of how many completions the current model has mad against other models while playing white
        #used to decide who plays what color during training
        self.whiteCompletionsPerBot = np.zeros(self.opponentNum, int)

        #an array that keeps track of how many games have been completed against other models
        self.completionsPerBot = np.zeros(self.opponentNum, int)

        #an array the keeps track of how many games have been attempted against other models
        self.gamesPerBot = np.zeros(self.opponentNum, int)

        #the list of bots that have already been loaded into the session
        #indexed by offset value (loadedBots[n] => model_"(maxIndex - n)".keras)
        self.loadedBots = []

        #generate the scheduled games
        self.broadGameSchedule = getGameDist(self.broadGameCount, self.opponentNum)
        self.narrowGameSchedule = np.zeros(self.opponentNum)

        self.botOffset = 0

        #play all the bots in the broad game schedule
        while self.botOffset != self.opponentNum:

            #load opponent bot (first one will be self)
            self.loadedBots.append(Network.Model(offset=self.botOffset))

            #play all the games against one bot
            self.playBot(self.broadGameSchedule[self.botOffset])

            self.botOffset += 1

        self.narrowGameSchedule = victorDistrobution(self.completionsPerBot, (self.completionsPerBot - self.winsPerBot), self.narrowGameCount)
        self.botOffset = 0

        #play all the bots in the narrow game schedule
        while self.botOffset != self.opponentNum:

            #play all the games against one bot
            self.playBot(self.narrowGameSchedule[self.botOffset])

            self.botOffset += 1

        preTrainCost = self.verifyTraining()

        #train on the data
        self.currentNetwork.model.fit(x=[self.boardTrainData, self.periTrainData], y=self.outputTrainData, batch_size=len(self.outputTrainData), epochs=60, verbose=0)

        postTrainCost = self.verifyTraining()

        self.moniterTraining(preTrainCost, postTrainCost)
        #self.validate()

    #play all the games against one specific bot and add the data to the training data
    def playBot(self, gameNum):

        #check if we have already finished our broad schedule
        if sum(self.narrowGameSchedule) != 0:
            #adjust gameNum
            gameNum += self.broadGameSchedule[self.botOffset]

        while self.completionsPerBot[self.botOffset] != gameNum:

            #play a game against the current bot (using implicit pass of botOffset from trainEpoch())
            outcome = self.playGame()

            self.gamesPerBot[self.botOffset] += 1

            if outcome:
                self.completionsPerBot[self.botOffset] += 1
                winner = not self.game.board.turn

                #get dataset
                winnerBoards = self.game.players[winner].positions
                loserBoards = self.game.players[not winner].positions
                winnerPeri = self.game.players[winner].peripherals
                loserPeri = self.game.players[not winner].peripherals

                #I can't use a fixed offset (-1 or 1) for my evaluation, because worse positions will receive higher gradients.
                #I can't use logged evaluations, because they may conform my network to previous versions.

                #The best strategy will be to evaluate all the positions with the current network, and accept the error between
                #different models choices.

                winnerEvaluations = self.currentNetwork.model.predict_on_batch([np.array(winnerBoards), np.array(winnerPeri)]).T[0]
                loserEvaluations = self.currentNetwork.model.predict_on_batch([np.array(loserBoards), np.array(loserPeri)]).T[0]

                #apply correction to the model
                winnerOutput = np.clip(reinforcedEval(winnerEvaluations, True, self.nominalWinGain, self.blunderCatcherGain), -1.0, 1.0)
                loserOutput = np.clip(reinforcedEval(loserEvaluations, False, self.nominalWinGain, self.blunderCatcherGain), -1.0, 1.0)
                self.boardTrainData = np.concatenate((self.boardTrainData, winnerBoards, loserBoards), axis=0)
                self.periTrainData = np.concatenate((self.periTrainData, winnerPeri, loserPeri), axis=0)
                self.outputTrainData = np.concatenate((self.outputTrainData, winnerOutput, loserOutput), axis=0)

                #check if the bot that one was the main bot
                if (self.colorSelect == winner):
                    #add one to the appropriate tally
                    self.winsPerBot[self.botOffset] += 1

                #check if the main bot was white
                if (self.colorSelect == chess.WHITE):
                    #add one to the appropriate tally
                    self.whiteCompletionsPerBot[self.botOffset] += 1

            self.moniterSchedule()

    #play a game to its end, and return the outcome
    def playGame(self):

        if self.completionsPerBot[self.botOffset] != 0 and self.whiteCompletionsPerBot[self.botOffset] / float(self.completionsPerBot[self.botOffset]) < 0.5:
            self.colorSelect = chess.WHITE
        elif self.completionsPerBot[self.botOffset] != 0 and self.whiteCompletionsPerBot[self.botOffset] / float(self.completionsPerBot[self.botOffset]) > 0.5:
            self.colorSelect = chess.BLACK
        else:
            self.colorSelect = bool(random.getrandbits(1))

        #train bot gets white
        if self.colorSelect:
            whiteBot = self.currentNetwork
            blackBot = self.loadedBots[self.botOffset]
        #train bot gets black
        else:
            whiteBot = self.loadedBots[self.botOffset]
            blackBot = self.currentNetwork

        self.white = Players.Bot(chess.WHITE, whiteBot, self.confidence)
        self.black = Players.Bot(chess.BLACK, blackBot, self.confidence)
        self.game = Game.Game([self.black, self.white], display=False)

        while self.game.isEnd() == False:

            self.game.makeMove()

        #if the game ended in a win, return True
        if self.game.board.is_checkmate():

            return True
        
        else:

            return False
        
    #check how well the model conformed to the training
    def verifyTraining(self):

        cost = keras.losses.mean_absolute_error(self.outputTrainData, self.currentNetwork.model.predict_on_batch([np.array(self.boardTrainData), np.array(self.periTrainData)]).T[0])
        return cost.numpy()

    #test the network on some archived positions (not for training...just a way to reality check)
    def validate(self):

        return self.currentNetwork.model.evaluate(self.testPos, self.testEval)

    #handle monitering system for playing schedule (something lightweight)
    def moniterSchedule(self):


        if sum(self.gamesPerBot) != 1:
            #clear lines
            print("\033[F" * 7)
        else:
            print("-" * 60)

        remainingGames = sum(self.broadGameSchedule) + sum(self.narrowGameSchedule) - sum(self.completionsPerBot)

        #print remaining games
        if sum(self.completionsPerBot) != 0:
            print("Games to play: " + str(int(remainingGames)) + " | Games completed: " + str(int(sum(self.completionsPerBot))) + " | Win ratio: " + str(int(sum(self.winsPerBot) / sum(self.completionsPerBot) * 100)) + " %   ")
        else:
            print("Games to play: " + str(int(remainingGames)) + " | Games completed: " + str(int(sum(self.completionsPerBot))) + " | Win ratio: 0 %   ")

        #print total wins
        print("Wins against each bot: ", end='')
        print(self.winsPerBot.tolist())

        #print total completions
        print("Completions against each bot: ", end='')
        print(self.completionsPerBot.tolist())

        #print total games
        print("Games against each bot: ", end='')
        print(self.gamesPerBot.tolist())

        print("Completed epochs: ", end='')
        print(self.epochCount)

        print("-" * 60)

    #handle monitering system for training
    def moniterTraining(self, startCost, endCost):

        print("Training on " + str(len(self.boardTrainData)) + " dataSets...")
        print("Starting cost: " + f"{startCost:.3}" + " | Final cost: " + f"{endCost:.3}")

#get a distibution of opponents given a number of games to play (play better bots more)
def getGameDist(gameNum, opponentNum):
    gameList = np.zeros(opponentNum)
    for i in range(0, opponentNum):
        gameList[i] = gameDist(i, opponentNum)
    gameList = (gameList * gameNum).astype(int)
    return gameList

#game distibution function --> used in getGameDist
def gameDist(index, n):

    return 1 / n

#reward function
def reinforcedEval(evals, winner, nominal, blunderCatcherGain):

    # Determine where the eval at a specific move is greater than the
    # move after it.  In such a case, it is perhaps adventagous to 
    # manually adjust the evaluation to match that of the move after
    # to maintain search depth consistency.
    #
    # The goal is that the bot will be encouraged to evaluate more
    # consistently into the future of the game, futher pressuring the
    # evaluation to reflect the true status of the game.
    #
    # In an optimal performance, my game evaluation should only ever go up.
    # If it goes down, it means that there was an optimal response by the
    # opponent that the bot hadn't seen, and the position truly is not as
    # good as it at first thought.
    evalDropMask = np.less(evals[1:], evals[:-1])

    # find sum of total adjustment across all positions
    adjustmentSum = np.sum(np.where(evalDropMask, blunderCatcherGain * (evals[:-1] - evals[1:]), 0))

    # overhaul evals based on the eval drop mask
    evals[:-1] += np.where(evalDropMask, blunderCatcherGain * (evals[1:] - evals[:-1]), 0)
    evals += adjustmentSum / len(evals)

    # apply adjustments based on win/lose status
    if winner == True:
        evals = evals + nominal * (1 - (evals + 1) / 2)
    else:
        evals = evals + -nominal * ((evals + 1) / 2)

    return evals

def victorDistrobution(gamesPlayed, gamesLost, gameNum):

    #take the normalized distrobution of losses to total games
    victorDist = (gamesLost / gamesPlayed) / sum(gamesLost / gamesPlayed)

    #multiply the distrobution by the number of games and cast to int
    victorGames = (victorDist * gameNum).astype(int)

    return victorGames
