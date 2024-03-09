#Test script: train the network for a certain volume of games

import lib.Trainer as Trainer

trainer = Trainer.Trainer()

trainer.trainSession(1, 5)