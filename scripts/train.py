#Test script: train the network for a certain volume of games

import lib.Trainer as Trainer

trainer = Trainer.Trainer(games=1, startNoise=0.09)

trainer.trainSession(1)