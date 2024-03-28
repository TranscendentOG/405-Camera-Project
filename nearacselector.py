def nearacselector(a): # Creates a function that takes the dictionary data and finds the closest aircraft
    print('Locating nearest aircraft...')
    acdst = [] # Creates an array to populate with aircraft distances
    achex = [] # Creates an array to populate with aircraft hex identifiers
    for items in a['ac']:
        acdst.append(items['dst']) # Populate array with aircraft distances
        achex.append(items['hex']) # Populate array with aircraft hex identifiers
    nearest = min(acdst) # Designate the nearest aircraft as the minimum distance
    for items in range(len(acdst)):
        if acdst[items] == nearest:
            global trackhex # Creates a global variable called trackhex to identify the aircraft with 
            trackhex = achex[items]
    print(f'The nearest aircraft is {nearest} NM from the device\'s location.')
    print(f'The nearest aircraft\'s hex identifier is {trackhex}.')
            
nearacselector(data)
