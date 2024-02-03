#Test script: replay a training game

import lib.Display as Display

while True:

    print('Which game index would you like to replay: ', end='')
    index = int(input())

    display = Display.Display()

    display.replay(index)

    print('Would you like to replay another game? (y/n): ', end='')
    answer = input()
    if answer == 'n':
        break