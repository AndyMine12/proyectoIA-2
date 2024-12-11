BASE_PATH = "base_r.txt"
WALL_PATH = "wall_index.txt"
OUTPUT_PATH = "heatmaps.txt"
SIMPLE_REWARD_OUT_PATH = "simple_reward.txt"
COMPOUND_REWARD_OUT_PATH = "compound_reward_30.txt"

#Used to monitor performance
import time 

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

#Utility to help traverse the map. Returns new position in map or -1 if the desired action is illegal
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

#Construct dictionary with all possible combinations of ghost positions for a given player position (with associated heatmaps)
def build_ghost_shifted(player_pos:int, dimension:tuple[int,int], value:int = 400, decay:int = 50, base_matrix:list[int] = load_base(), wall_index:list[int] = load_walls(), is_conmutative:bool = False) -> dict[tuple[int,int],list[int]]:
    effective_range = []
    for i in range(dimension[0]*dimension[1]):
        if i not in wall_index:
            effective_range.append(i)

    if (player_pos not in effective_range):
        raise ValueError("Player is not in a valid position. Cannot construct heatmaps")
    
    r_heatmap_dict:dict[tuple[int,int],list[int]] = dict()

    for ghost1_pos in effective_range:
        for ghost2_pos in effective_range:
            if (ghost1_pos != ghost2_pos):
                if (ghost1_pos < ghost2_pos) or (not is_conmutative):
                    state = (ghost1_pos, ghost2_pos, player_pos)
                    ghost_pos = (ghost1_pos,ghost2_pos)
                    r_heatmap_matrix:list[int] = populate_matrix(base_matrix.copy(), dimension, state, None, value, decay) 
                    r_heatmap_dict[ghost_pos] = r_heatmap_matrix
    return r_heatmap_dict   

#Construct dictionary with all possible state combinations. Keys are the player's states and value are dictionaries that contain r-matrixes as values and ghost-positions as keys
def build_full_shifted(dimension:tuple[int,int], value:int = 400, decay:int = 50, base_matrix:list[int] = load_base(), wall_index:list[int] = load_walls(), verbose:bool = False, is_conmutative:bool = False) -> dict[int,dict[tuple[int,int],list[int]]]:
    effective_range = []
    for i in range(dimension[0]*dimension[1]):
        if i not in wall_index:
            effective_range.append(i)
    
    heatmap_dict:dict[int,dict[tuple[int,int],list[int]]] = dict()

    print_acc = [0, 1]
    timestamp = time.time()
    for position in effective_range:
        r_heatmap_dict = build_ghost_shifted(position, dimension, value, decay, base_matrix, wall_index, is_conmutative)
        heatmap_dict[position] = r_heatmap_dict
        if (verbose):
            print_acc[0] += 1
            if ( print_acc[0] >= len(effective_range)*0.05 ):
                print(f"Full build {print_acc[1]*5}% done (in {round(time.time() - timestamp, 4)}s)")
                print_acc[0] = 0
                print_acc[1] += 1
    if (verbose):
        print(f"Full build completed in {round(time.time() - timestamp, 4)}s")
    return heatmap_dict

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

#Save a full heatmap - with all possible state configurations - into target file. If it already exists, overwrites it.
#NOTE This can also be used to save r-matrixes since they have the same structure, only with different values inside. Whoops.
def save_full_matrix(full_matrix:dict[int,dict[tuple[int,int],list[int]]], filename:str, verbose:bool = False) -> None:
    print_acc = [0,1]
    timestamp = time.time()
    with open(filename, 'w') as file:
        for player_pos in full_matrix.keys():
            for ghost_pos in full_matrix[player_pos].keys():
                state_str = str(ghost_pos[0]) + "|" + str(ghost_pos[1]) + "|" + str(player_pos)
                data_str = ""
                current_matrix = full_matrix[player_pos][ghost_pos]
                for index,value in enumerate(current_matrix):
                    data_str += str(value)
                    if index < (len(current_matrix) - 1):
                        data_str += "|"
                file.write(state_str + " = " + data_str + "\n")

            if (verbose):
                print_acc[0] += 1
                if ( print_acc[0] >= len(full_matrix.keys())*0.05 ):
                    print(f"Saving {print_acc[1]*5}% done (in {round(time.time() - timestamp, 4)}s)")
                    print_acc[0] = 0
                    print_acc[1] += 1
    if (verbose):
        print(f"Saving completed in {round(time.time() - timestamp, 4)}s")

#Generate r-matrixes using generated heatmaps as starting point. Adjacent player states represent ghost-shifted matrixes with player positions as where player may stand on time t+1. Returns state->action matrix. Actions sorted by sequence (0,0), (0,1), (0,2), ...
#If time_multiplier is non-zero, and adjacent-player-states is not None, compounds available reward for time t with available reward for time t+1.
def to_reward_matrix(ghost_shifted_matrix:dict[tuple[int,int], list[int]], dimension:tuple[int,int], time_multiplier:float = -1.0, adjacent_player_states:list[ dict[tuple[int,int], list[int]] ] = None) -> dict[tuple[int,int], list[int]]:
    reward_matrix: dict[tuple[int,int], list[int]] = dict()
    for state in ghost_shifted_matrix.keys():
        action_list: list[int] = []
        for action_g1 in range(4): #Try every possible action (north, east, south, west)
            newPos_g1 = parse_action(state[0], action_g1, dimension)
            for action_g2 in range(4): #Try every possible action
                newPos_g2 = parse_action(state[1], action_g2, dimension)

                #Get reward from present time
                heatmap:list[int] = ghost_shifted_matrix[state]
                reward:int = -1
                if (action_g1 != -1) and (action_g2 != -1) and (heatmap[newPos_g1] != -1) and (heatmap[newPos_g2] != -1):
                    reward = heatmap[newPos_g1] + heatmap[newPos_g2]
                if (max(heatmap) < 1): #There are no rewards on map. Thus, Pacman was captured. All actions should be tagged as illegal
                    reward = -1

                #Compose with projected reward in future states, if available
                if ( (time_multiplier > 0) and (adjacent_player_states is not None) ):
                    if (reward != -1):
                        for future_ghost_matrix in adjacent_player_states:
                            future_heatmap:list[int] = future_ghost_matrix[state]
                            reward += round(time_multiplier * (future_heatmap[newPos_g1] + future_heatmap[newPos_g2]))
                elif ( (time_multiplier > 0) or (adjacent_player_states is not None) ): #Show warning if future states are badly configured - if at least one of them is correct. Else, assume that future projection is unavailable/not desired
                    print('\033[93m' + "WARN" + "\033[0m" + ". Time multiplier (must be higher than zero) or adjacent states (must be not None) not valid. Ignoring time projection.")
                
                action_list.append(reward)
        reward_matrix[state] = action_list
    return reward_matrix

#Generate r-matrixes using fully generated heatmap combinations as starting point. Adjacent player states represent ghost-shifted matrixes with player positions as where player may stand on time t+1. Returns state->action matrix. Actions sorted by sequence (0,0), (0,1), (0,2), ...
#If time multiplier is non-zero, compounds available reward for time t with available reward on time t+1
def to_reward_combination(full_heatmap:dict[int,dict[tuple[int,int],list[int]]], dimension:tuple[int, int], time_multiplier:float = -1.0, verbose:bool = False) -> dict[int,dict[tuple[int,int],list[int]]]:
    full_reward_matrix:dict[int,dict[tuple[int,int],list[int]]] = dict()
    
    print_acc:list[int] = [0,1]
    timestamp:float = time.time() #Monitor performance
    for player_pos in full_heatmap.keys():
        adjacent_heatmap_list = None
        if (time_multiplier > 0):
            adjacent_heatmap_list = []
            for action in range(4): #Try with all possible player movements (North, East, South, West)
                newPos:int = parse_action(player_pos, action, dimension)
                if (newPos in full_heatmap.keys()):
                    adjacent_heatmap_list.append(full_heatmap[newPos])
        
        reward_matrix = to_reward_matrix(full_heatmap[player_pos], dimension, time_multiplier, adjacent_heatmap_list)
        full_reward_matrix[player_pos] = reward_matrix

        if (verbose):
            print_acc[0] += 1
            if ( print_acc[0] >= len(full_heatmap.keys())*0.05 ):
                print(f"Reward combination {print_acc[1]*5}% done (in {round(time.time() - timestamp, 4)}s)")
                print_acc[0] = 0
                print_acc[1] += 1
    if (verbose):
        print(f"Reward combination completed in {round(time.time() - timestamp, 4)}s")
    return full_reward_matrix

if __name__ == "__main__": #Only execute building commands if this is the main file being executed
    #* Remove comments below to construct regular, non-conmutative, reward matrixes

    # #Now, we test full build and saving to file
    # full_heatmap = build_full_shifted((18,9), 400, 50, verbose=True)
    # # print("Trying to save to txt file...") #WARNING. File weights ~520Mb
    # # save_full_matrix(full_heatmap, OUTPUT_PATH, True)

    # #After, we test building action->reward matrixes without time projection
    # print("Simple reward construction")
    # simple_reward = to_reward_combination(full_heatmap, (18,9), -1, True)
    # save_full_matrix(simple_reward, SIMPLE_REWARD_OUT_PATH, True)

    # #Finally, add time projection with 0.30 multiplier
    # print("Compound reward construction (0.30 time multiplier)")
    # compound_reward_30 = to_reward_combination(full_heatmap, (18,9), 0.3, True)
    # save_full_matrix(compound_reward_30, COMPOUND_REWARD_OUT_PATH, True)


    #* Remove comments below to construct conmutative reward matrixes
    full_conm_heatmap = build_full_shifted((18,9), 400, 50, verbose=True, is_conmutative=True)
    print("Reward construction")
    conm_reward = to_reward_combination(full_conm_heatmap, (18,9), 0.3, True)
    save_full_matrix(conm_reward, "conm_compound_reward_30.txt", True)

    #* Remove comments below to test ghost matrix traversal

    # empty_matrix = load_base()
    # state_so = (79,82,154) #154
    # conf_so = populate_matrix(empty_matrix.copy(), (18,9), state_so, None, 400, 50)

    # initial_time = time.time()
    # shift_so = build_ghost_shifted(state_so[2], (18,9))
    # print(f"Operation done in {time.time() - initial_time} seconds")

    # #Finally, we show
    # traverse_ghost_matrix(shift_so, (18,9), state_so)
