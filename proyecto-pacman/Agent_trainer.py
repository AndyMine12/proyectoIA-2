from Rmatrix_populator import parse_action, save_full_matrix, print_matrix, load_base, load_walls

R_MATRIX_PATH = "conm_compound_reward_30.txt"

#Used to monitor performance
import time 
# Print time taken (in seconds) to sucessfully compute the given function call
def performance_decorator(function):
    def wrapper(*args, **kwargs):
        timestamp = time.time()
        result = function(*args, **kwargs)
        print(f"{function.__name__} completed in {round(time.time() - timestamp, 4)}s")
        return result
    
    return wrapper

#Initialize a qtable from a given reward table 
def qtable_initializer(r_table:dict[tuple[int,int], list[int]]) -> dict[tuple[int,int], list[int]]:
    q_table:dict[tuple[int,int], list[int]] = dict()
    for state in r_table.keys():
        q_table[state] = [0 for action in r_table[state]]
    return q_table

@performance_decorator
#Initialize a combination of qtables from a given combination of reward tables
def qmatrix_initializer(r_matrix:dict[int,dict[tuple[int,int],list[int]]]) -> dict[int,dict[tuple[int,int],list[int]]]:
    q_matrix:dict[int,dict[tuple[int,int],list[int]]] = dict()
    for player_pos in r_matrix.keys():
        q_table = qtable_initializer(r_matrix[player_pos])
        q_matrix[player_pos] = q_table
    return q_matrix

@performance_decorator
def load_full_matrix(filename:str, dimension:tuple[int,int], verbose:bool = False) -> dict[int,dict[tuple[int,int],list[int]]]:
    matrix:dict[int,dict[tuple[int,int],list[int]]] = dict()
    prev_player_pos:int = -1
    
    with open(filename, 'r') as file:
        all_lines:list[str] = file.readlines()
        print_acc:list[int] = [0,1]
        timestamp:int = time.time()
    
        for index, line in enumerate(all_lines):
            line = line.strip("\n").strip()
            if (line != ""):
                line_split = line.split("=")
                if (len(line_split) != 2):
                    raise ValueError(f"ERROR. Badly formatted line on file {filename}. Error found at line {index}. Should have key=value pairs.")
                
                state = line_split[0].strip().split("|")
                if (len(state) != 3):
                    raise ValueError(f"ERROR. Badly formatted line on file {filename}. Error found at line {index}. State should have ONLY 3 values")
                for value in state:
                    if (not value.isdigit()):
                        raise ValueError(f"ERROR. Badly formatted line on file {filename}. Error found at line {index}. State should be an INTEGER tuple separated with pipes like 1|2|3")
                    elif( (int(value) < 0) or (int(value) >= dimension[0]*dimension[1]) ):
                        raise ValueError(f"ERROR. Badly formatted line on file {filename}. Error found at line {index}. Given dimension {dimension[0]}x{dimension[1]}, position must be between 0 and {dimension[0]*dimension[1] - 1} inclusive")
                state = [int(value) for value in state]
                    
                reward = line_split[1].strip().split("|")
                if (len(reward) != 16):
                    raise ValueError(f"ERROR. Badly formatted line on file {filename}. Error found at line {index}. There should be rewards registered for 16 different actions")
                for value in reward:
                    if ( (not value.isdigit()) and not( (value[0] in "+-") and (value[1:].isdigit()) ) ):
                        raise ValueError(f"ERROR. Badly formatted line on file {filename}. Error found at line {index}. Actions' rewards should be an INTEGER tuple separated with pipes like 1|2|3")
                reward = [int(value) for value in reward]

                if (prev_player_pos == -1): #Previous player position not initialized
                    prev_player_pos = state[2]
                    table:dict[tuple[int,int], list[int]] = dict()
                
                if (prev_player_pos == state[2]): #Previous player position same as current
                    table[(state[0], state[1])] = reward #Save state*action -> reward association for current state
                else: #Player position changed
                    matrix[prev_player_pos] = table #Commit finished table of all combinations within the previous player position into full dictionary
                    table = dict() #Reset dictionary for player position
                    table[(state[0], state[1])] = reward
                prev_player_pos = state[2] #Update previous player position for next line
            if (verbose):
                print_acc[0] += 1
                if (print_acc[0] >= len(all_lines)*0.1):
                    print(f"Matrix loading {print_acc[1]*5}% done (in {round(time.time() - timestamp, 4)}s)")
                    print_acc[0] = 0
                    print_acc[1] += 1
        matrix[prev_player_pos] = table #Commit the last table into the full dictionary
    if (verbose):
        print(f"Loading completed in {round(time.time() - timestamp, 4)}s")
    return matrix

rmatrix = load_full_matrix(R_MATRIX_PATH, (18,9))
qmatrix = qmatrix_initializer(rmatrix)

print(f"Total states Q|R -> {len(qmatrix.keys())}|{len(rmatrix.keys())}")
