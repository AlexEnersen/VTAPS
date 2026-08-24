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
                    newLine = f" {items[0]} {items[1]} {items[2]}  {newPop:>4}  {newPop:>4}     {items[5]}     {items[6]}    {items[7]}     {items[8]}     {items[9]}   {items[10]}   {items[11]}   {items[12]}   {items[13]}   {items[14]}                        {items[15]}\n"
                    text[i] = newLine
                    return text
        
    return text