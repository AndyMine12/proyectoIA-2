import json
BASE_PATH = "base_r.txt"
WALL_PATH = "wall_index.txt"

# NOTE - ALL state tuples are given as (ghost1-pos, ghost2-pos, player-pos)

#Load base r-matrix from specified file
def load_base(filename:str = BASE_PATH) -> list[int]:
    base_matrix:list[int] = []
    with open(filename, 'r') as file:
        file_str = file.read()
        for value in file_str.split("|"):
            base_matrix.append(int(value))
    return base_matrix
#Load index with all possible wall positions
def load_walls(filename:str = WALL_PATH) -> list[int]:
    wall_matrix:list[int] = []
    with open(filename, 'r') as file:
        file_str = file.read()
        for value in file_str.split("|"):
            wall_matrix.append(int(value))
    return wall_matrix

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
def populate_matrix(target:list[int], dimension:tuple[int,int], state:tuple[int,int,int], position:int = None, value:int = 400, decay:int = 50) -> list[int]:
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

#Construct dictionary with all possible combinations of ghost positions for a given player position
def build_ghost_shifted(player_pos:int, dimension:tuple[int,int], value:int = 400, decay:int = 50, base_matrix:list[int] = load_base(), wall_index:list[int] = load_walls()) -> dict[tuple[int,int],list[int]]:
    effective_range = []
    for i in range(dimension[0]*dimension[1]):
        if i not in wall_index:
            effective_range.append(i)
    
    r_dict:dict[tuple[int,int],list[int]] = dict()

    for ghost1_pos in effective_range:
        for ghost2_pos in effective_range:
            if (ghost1_pos != ghost2_pos):
                state = (ghost1_pos, ghost2_pos, player_pos)
                ghost_pos = (ghost1_pos,ghost2_pos)
                r_matrix:list[int] = populate_matrix(base_matrix.copy(), dimension, state, None, value, decay)
                r_dict[ghost_pos] = r_matrix
    return r_dict   

#Print matrix to console, showing values
def print_matrix(target:list[int], dimension:tuple[int,int], state:tuple[int,int,int]) -> None:
    def reduce(value:int, max_value:int) -> int:
        if (value < 0): #Do not reduce walls nor penalties
            return value
        if (max_value == 0): #Do not divide by zero, rather return identity
            return value
        proportion = (value / max_value) * 10
        return round(proportion)
    acc = 0
    row = 0
    max_value = max(target)

    for square in target:
        square_norm:int = reduce(square, max_value)
        if ( (square_norm == 0) and (square == 0) ):
            if ( (acc + row*dimension[0]) == state[0] ): #Show ghost's position as blue
                print("\033[94m" + "S" + "\033[0m", end="")
            elif ( (acc + row*dimension[0]) == state[1] ):
                print("\033[94m" + "Z" + "\033[0m", end="")
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

#Traverse a given player position combination with action commands to see influence of ghost position
def traverse_ghost_matrix(ghost_shifted_matrix:dict[tuple[int,int],list[int]], dimension:tuple[int,int], initial_state:tuple[int,int,int]) -> None:
    action:str = "0"
    state:tuple[int,int,int] = initial_state

    print(f"GHOST SIMULATION START ({state[2]})")
    print("[INSERT -1 TO QUIT]")
    while (action != "-1"):
        current_map = ghost_shifted_matrix[(state[0], state[1])]
        print_matrix(current_map, dimension, state)
        action = str(input("> "))

        if (action == "-1"):
            print("GHOST SIMULATION END\n")
        elif (len(action) != 2):
            print("ERROR. Must pick two actions")
        elif (not action.isdigit()):
            print("ERROR. Only insert numeric actions in order (e.g. 01 to move ghosts north, east respectively)")
        else:
            newPos_g1:int = parse_action(state[0], int(action[0]), dimension)
            newPos_g2:int = parse_action(state[1], int(action[1]), dimension)
            if ( (newPos_g1 == -1) or (newPos_g2 == -1) ):
                print("Invalid action selected (Trying to move out-of-bounds)")
            elif ( (current_map[newPos_g1] == -1) or (current_map[newPos_g2] == -1) ):
                print("Invalid action selected (Cannot move into walls)")
            else:
                state = (newPos_g1, newPos_g2, state[2])

#Save a given matrix into the target file. If it already exists, overwrites it.
def save_matrix(filename:str, upd_matrix:list[int]) -> None:
    pass

#Test performance
import time 

#Now, we test
empty_matrix = load_base()
state_so = (79,82,154) #154
#conf_so = populate_matrix(empty_matrix.copy(), (18,9), state_so, None, 400, 50)
initial_time = time.time()
shift_so = build_ghost_shifted(state_so[2], (18,9))
print(f"Operation done in {time.time() - initial_time} seconds")
#Finally, we show
#print_matrix(conf_so, (18,9), state_so)
traverse_ghost_matrix(shift_so, (18,9), state_so)
