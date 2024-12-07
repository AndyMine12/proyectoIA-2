import json
BASE_PATH = "base_r.txt"

# NOTE - ALL state tuples are given as (ghost1-pos, ghost2-pos, player-pos)

#Load base r-matrix from specified file
def load_base(filename:str = BASE_PATH) -> list[int]:
    base_matrix:list[int] = []
    with open(filename, 'r') as file:
        file_str = file.read()
        for value in file_str.split("|"):
            base_matrix.append(int(value))
    return base_matrix

#Load given state's matrix from specified json file.
def load_matrix(filename:str, state:tuple[int,int,int], default_fallback:bool = False) -> list[int]:
    with open(filename, 'r') as file:
        with json.load(file) as data:
            result:list[int] = []
            try:
                result = (data[state[2]])[(state[0],state[1])] #Access value as top-level (player-position) then key (ghost-position as tuple)
            except Exception as error:
                if (default_fallback):
                    print("\033[93m" + "WARN" + "\033[0m" + ". Value not found. Assigning default")
                    result = load_base()
                else:
                    raise error
            return result

#Utility to help traverse the map. Returns -1 if the desired action is illegal
def parse_action(initial_pos:int, action:int, dimension:tuple[int,int]) -> int:
    match action:
        case -1: #Stay
            return initial_pos
        case 0: #Move North
            candidate = initial_pos - dimension[0]
            if ( candidate < 0 ):
                return -1
            return candidate
        case 1: #Move East
            if ( (initial_pos % dimension[0]) == (dimension[0] - 1) ):
                return -1
            return (initial_pos + 1)
        case 2: #Move South
            candidate = initial_pos + dimension[0]
            if ( candidate > ((dimension[0]*dimension[1])-1) ):
                return -1
            return candidate
        case 3: #Move West
            if ( (initial_pos % dimension[0]) == (0) ):
                return -1
            return (initial_pos - 1)
        case _: #Illegal action
            raise ValueError("Action can only be stay (-1); or move north (0), east (1), south (2) or west (3)")

#Populate given matrix with heatmap
def populate_matrix(target:list[int], dimension:tuple[int,int], state:tuple[int,int,int], position:int = None, value:int = 200, decay:int = 40) -> list[int]:
    if (position is None):
        position = state[2]

    if ( (state[0] != position) and (state[1] != position) and (target[position] != -1) ): #Do not spread past ghosts nor walls
        if (target[position] < value):
            target[position] = value
            if ( (value - decay) > 0 ):
                for action in range(4):
                    newPos:int = parse_action(position, action, dimension)
                    if (newPos != -1): #If the move was legal, spread heat
                        target = populate_matrix(target, dimension, state, newPos, value - decay, decay)
    return target

#Print matrix to console, showing values
def print_matrix(target:list[int], dimension:tuple[int,int], state:tuple[int,int,int], max_value:int) -> None:
    def reduce(value:int, max_value:int) -> int:
        if (value < 0): #Do not reduce walls nor penalties
            return value
        proportion = (value / max_value) * 10
        return round(proportion)
    acc = 0
    row = 0

    for square in target:
        square_norm:int = reduce(square, max_value)
        if ( (square_norm == 0) and (square == 0) ):
            if ( (acc + row*dimension[0]) == state[0] ) or ( (acc + row*dimension[0]) == state[1] ): #Show ghost's position as blue
                print("\033[94m" + "S" + "\033[0m", end="")
            else: #Empty spaces are white
                print("O", end="")
        elif square_norm >= 0:
            if (square_norm > 9): #Show Pac-man's location as yellow
                print("\033[93m\033[1m" + "C" + "\033[0m", end="")
            else: #Show other 'hot' places as green
                print("\033[92m" + str(square_norm) + "\033[0m", end="")
        else: #Show walls as red
            print("\033[91m" + "#" + "\033[0m", end="")
        acc += 1
        if (acc >= dimension[0]):
            acc = 0
            row += 1
            print()

#Now, we test
empty_matrix = load_base()
state_so = (79,82,77)
conf_so = populate_matrix(empty_matrix.copy(), (18,9), state_so, None, 200, 20)
#Finally, we show
print_matrix(conf_so, (18,9), state_so, 200)
