def setSeedingRate(text, seedingRate):
    ## 4046.86 square-meters in 1 acre
    newPop = round(float(seedingRate) / 4046.86, 1)
    planting = 0
    for i, line in enumerate(text):

        items = line.split(" ")
        items = [x for x in items if x]
        if len(items) > 0:
            if items[0] == "*PLANTING":
                planting += 1
            elif planting > 0:
                planting += 1
                if planting == 3:
                    newLine = f" 1 20122 20135  {newPop:>4}  {newPop:>4}     S     R    76     0     5   -99   -99   -99   -99   -99                        Maize\n"
                    text[i] = newLine
                    return text
        
    return text