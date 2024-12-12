from Rmatrix_populator import load_base, load_walls
from GhostAI import GhostAI

#Used to monitor performance
import time 
from Performance_util import performance_decorator, get_timestamp

R_MATRIX_PATH = "output-files/rmatrix_v2.txt"
Q_MATRIX_PATH = "output-files/qmatrix.txt"
LOAD_Q_MATRIX = False
DEFAULT_ERROR_RECORD_PATH = "output-files/ai-error-records/"

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

if __name__ == "__main__":
    #Get full r-matrix from disk and initialize q-matrix
    rmatrix = load_full_matrix(R_MATRIX_PATH, (18,9))
    if (not LOAD_Q_MATRIX):
        qmatrix = qmatrix_initializer(rmatrix)
    else:
        qmatrix = load_full_matrix(Q_MATRIX_PATH, (18,9))
    print(f"Total states Q|R -> {len(qmatrix.keys())}|{len(rmatrix.keys())}")

    #Initialize states and ai_brain
    state_so = (79,82,154)
    ai_brain = GhostAI(state_so, load_walls(), (18,9), qmatrix, 1)

    #Load all target positions
    target_positions:list[int] = []
    walls = load_walls()
    for i in range(18*9):
        if i not in walls:
            target_positions.append(i)

    acc = 25
    for position in target_positions:
        episode_count = 10000
        max_steps = 3000
        print(f"Training begin ({position}). {episode_count} Episodes of maximum {max_steps} steps each")
        ai_brain.update_player_pos(position)
        error_list = ai_brain.simulate_train(rmatrix, True, 0.7, 0.05, 0.15, episode_count, max_steps, round(episode_count/10))
        print(f"Training ended ({position}). Error: {error_list[-1]}")

        #SAVE ERROR RECORDS
        error_record_filename = DEFAULT_ERROR_RECORD_PATH + "record-" + str(position) + "_" + str(round(error_list[-1], 4)) + "_" + get_timestamp() + ".csv"
        with open(error_record_filename, 'w') as file:
            for index,value in enumerate(error_list):
                file.write(str(value))
                if index < (len(error_list) - 1):
                    file.write(",")
        print(f"Error records saved sucessfully at {error_record_filename}")

        acc -= 1
        if (acc <= 0):
            ai_brain.save_matrix()
            acc = 25
    
    #* SAVE Q-MATRIX
    ai_brain.save_matrix()

    #* ONLY SAVE UPDATED TABLE
    # ai_brain.save_table()
    # print("Table saved sucessfully")