#Test script: train the network for a certain volume of games

import lib.Trainer as Trainer

trainer = Trainer.Trainer(opponentNum=2)

trainer.trainSession(1, 20)