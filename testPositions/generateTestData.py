import csv
import sys
import numpy as np
import chess
import random

path = sys.path[0]

testDatasetCount = 600
        
#the index location of each piece type (aux, pawn, rook, knight, bishop, queen, king)
pieceIndex = {
    chess.PAWN : 0,
    chess.KNIGHT : 2 * 64,
    chess.BISHOP : 4 * 64,
    chess.ROOK : 6 * 64,
    chess.QUEEN : 8 * 64,
    chess.KING : 10 * 64
}

#the index offset of each piece color (my piece, other player's piece)
colorOffset = {
    chess.WHITE : 0,
    chess.BLACK : 64
}

#adjust a square index by color
def squareIndex(square, color):
    if color == chess.BLACK:
        return 63 - square
    else:
        return square

def getBitBoard(board):

    currentMap = board.piece_map()
    boardPos = np.zeros(12*64 + 1, np.bool_)
    color = not board.turn

    for square in currentMap:

        #add piece to the bit map
        boardPos[pieceIndex[currentMap[square].piece_type] + colorOffset[color == currentMap[square].color] + squareIndex(square, color)] = True

    return boardPos

with open(path + '\\chessData.csv', 'r') as testDataFile:

    reader = csv.reader(testDataFile)

    data = []

    for row in reader:
        if row != []:
            if row[1][0] == '#':
                data.append([row[0], row[1][1:]])
            else:
                data.append([row[0], row[1]])

testDataFile.close()


random.shuffle(data)

chooseData = data[0:testDatasetCount]

testDataPos = np.zeros((testDatasetCount, 12*64 + 1), np.bool_)
testDataEval = np.zeros(testDatasetCount)

for i in range(0, testDatasetCount):
    board = chess.Board(chooseData[i][0])
    testDataPos[i] = getBitBoard(board)
    testDataEval[i] = np.tanh(int(chooseData[i][1]) / 400) * int(board.turn)
    print(testDataEval[i])

np.save(path + '\\testPositions.npy', testDataPos)
np.save(path + '\\testEvaluations.npy', testDataEval)
