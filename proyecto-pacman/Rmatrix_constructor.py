IN_FILENAME = "map.txt"
OUT_FILENAME = "base_r.txt"
WALL_FILENAME = "wall_index.txt"
base_map: list[int] = []
wall_index: list[int] = []

#LOAD MAP
with open(IN_FILENAME, 'r') as file:
    map_height:int = 0
    map_width:int = -1
    for row,line in enumerate(file.readlines()):
        map_height += 1
        line = line.strip("\n")

        if (map_width == -1):
            map_width = len(line)
        elif (map_width != len(line)):
            raise ValueError("Map must be of fixed width")
        
        for i in range(map_width):
            base_map.append(0)

        for column,char in enumerate(line):
            if (char == "O"):
                base_map[map_width*row + (column)] = 0 #Set current square as 'legal' move
            elif (char == "X"):
                base_map[map_width*row + (column)] = -1 #Set current square as 'illegal' move
                wall_index.append(map_width*row + (column))
            else:
                raise ValueError("Squares must be either spaces (O) or walls (X)")
    
    print(f"SIZE {map_width}x{map_height}")
    acc = 0
    for square in base_map:
        if square == 0:
            print("O", end="")
        else:
            print("\033[91m" + "X" + "\033[0m", end="")
        acc += 1
        if (acc >= map_width):
            acc = 0
            print()
    print(f"\nWALLS ({len(wall_index)})\n",wall_index)

#SAVE BASE R-MATRIX
with open(OUT_FILENAME, 'w') as file:
    for index,value in enumerate(base_map):
        file.write(str(value))
        if index < (len(base_map) - 1):
            file.write("|")
    print(f"\nSaved result to file at ({OUT_FILENAME})")

#SAVE WALL INDEX
with open(WALL_FILENAME, 'w') as file:
    for index,value in enumerate(wall_index):
        file.write(str(value))
        if index < (len(wall_index) - 1):
            file.write("|")
    print(f"Also, saved wall index to file at ({WALL_FILENAME})")