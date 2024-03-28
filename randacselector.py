import random

def randacselector(a): # Creates a function that takes the dictionary data and randomly selects an aircraft
    print('Locating random aircraft...')
    b = random.randint(0,len(a['ac']))
    randst = a['ac'][b]['dst']
    global trackhex
    trackhex = a['ac'][b]['hex']
    print(f'The randomly selected aircraft is {randst} NM from the device\'s location.')
    print(f'The randomly selected aircraft\'s hex identifier is {trackhex}.')
    
randacselector(data)
