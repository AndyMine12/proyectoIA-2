import random
from Rmatrix_populator import save_full_matrix
from Performance_util import get_timestamp, performance_decorator

DEFAULT_SAVE_PATH = "output-files/ai-tables/"

class GhostAI:
    #Initialize GhostAI model. future_factor is gamma (discount for future actions versus value of present ones) and learn_rate is alpha
    def __init__(self, initial_state:tuple[int,int,int], wall_index:list[int], dimension:tuple[int,int], q_matrix:dict[int,dict[tuple[int,int],list[int]]], epsilon:float):
        self._q_matrix = q_matrix
        self._wall_index = wall_index
        self._dimension = dimension
        self.update_self_pos((initial_state[0], initial_state[1]))
        self.update_player_pos(initial_state[2])

        self._epsilon = epsilon
        self._do_explore = True

        random.seed() #Initialize random generator seed
    
    def update_self_pos(self, position:tuple[int,int]):
        if (position[0] < position[1]):
            self._lower_pos = position[0]
            self._higher_pos = position[1]
            self._inverted_pos:bool = False
        else:
            self._lower_pos = position[1]
            self._higher_pos = position[0]
            self._inverted_pos:bool = True
    
    def randomize_pos(self):
        #Pick position
        newPos = random.choices(list(self._q_matrix.keys()), k=2)
        newPos.sort()
        need_check:bool = True
        #Assert that ghosts are in different squares and are not over the player
        while (need_check):
            if newPos[0] == self._player_pos:
                newPos[0] += 1
            elif newPos[1] == self._player_pos:
                newPos[1] += 1
            elif newPos[0] in self._wall_index:
                newPos[0] += 1
            elif newPos[1] in self._wall_index:
                newPos[1] += 1
            elif newPos[0] == newPos[1]:
                newPos[1] += 1
            elif (newPos[0] > (self._dimension[0]*self._dimension[1] - 1)):
                newPos[0] = 0
            elif (newPos[1] > (self._dimension[0]*self._dimension[1] - 1)):
                newPos[1] = 0
            else:
                need_check = False
        #Decide if ghosts appear in normal or inverted position
        if random.random() > 0.5:
            newPos.sort(reverse=True)
        else:
            newPos.sort()
        #Update position
        self.update_self_pos(newPos)
    
    def update_player_pos(self, position:int):
        self._player_pos = position
    
    @property
    def state(self) -> tuple[int, int, int]:
        if (self._inverted_pos):
            return (self._higher_pos, self._lower_pos, self._player_pos)
        else:
            return (self._lower_pos, self._higher_pos, self._player_pos)
    
    @property
    def ghost_pos(self) -> tuple[int, int]:
        if (self._inverted_pos):
            return (self._higher_pos, self._lower_pos)
        else:
            return (self._lower_pos, self._higher_pos)

    @property
    def epsilon(self) -> float:
        return self._epsilon
    @epsilon.setter
    def epsilon(self, value):
        self._epsilon = value
    
    #Saves current q-matrix to file
    @performance_decorator
    def save_matrix(self, filename:str = DEFAULT_SAVE_PATH + "GhostAI_" + get_timestamp() + ".txt") -> None:
        save_full_matrix(self._q_matrix, filename)
    #Saves table corresponding to current player position to file
    def save_table(self, filename:str = None):
        if (filename is None):
            filename = DEFAULT_SAVE_PATH + "Table-" + str(self._player_pos) + "_" + get_timestamp() + ".txt"
        fake_matrix = {self._player_pos:self._q_matrix[self._player_pos]}
        save_full_matrix(fake_matrix, filename)

    #Parses and determinates if proposed action is legal (and returns new positions if so) or not (returns -1,-1)
    def parse_action(self, action_tuple:tuple[int, int]) -> tuple[int, int]:
        newPos:list[int] = []
        for oldPos, action in zip(self.ghost_pos, action_tuple):
            match action:
                case 0: #Move north
                    candidate = oldPos - self._dimension[0]
                    if (candidate < 0):
                        newPos.append(-1)
                    elif (candidate in self._wall_index):
                        newPos.append(-1)
                    else:
                        newPos.append(candidate)
                case 1: #Move east
                    candidate = oldPos + 1
                    if ( (oldPos % self._dimension[0]) == (self._dimension[0] - 1) ):
                        newPos.append(-1)
                    elif (candidate in self._wall_index):
                        newPos.append(-1)
                    else:
                        newPos.append(candidate)
                case 2: #Move south
                    candidate = oldPos + self._dimension[0]
                    if (candidate > ((self._dimension[0]*self._dimension[1])-1)):
                        newPos.append(-1)
                    elif (candidate in self._wall_index):
                        newPos.append(-1)
                    else:
                        newPos.append(candidate)
                case 3: #Move west
                    candidate = oldPos - 1
                    if ( (oldPos % self._dimension[0]) == (0) ):
                        newPos.append(-1)
                    elif (candidate in self._wall_index):
                        newPos.append(-1)
                    else:
                        newPos.append(oldPos - 1)
        if (newPos[0] == newPos[1]): #Ghosts cannot land on the same square
            newPos = [-1,-1]
        return tuple(newPos)
    
    #Return list with all available actions for current state
    def get_available_actions(self) -> list[tuple[int,int]]:
        action_list:list[tuple[int,int]] = []
        for i in range(16):
            action = (i//4, i%4)
            result = self.parse_action(action)
            if ( (result[0] != -1) and (result[1] != -1) ):
                action_list.append(action)
        return action_list
    
    #Transform action tuple into integer index, for using with q-tables
    def get_action_index(self, action:tuple[int,int]) -> int:
        return (action[0] * 4 + action[1])

    #Picks an action tuple from the available legal actions using e-greedy
    def pick_action(self, ignore_epsilon:bool = False) -> tuple[int,int]:
        q_table = self._q_matrix[self._player_pos]
        reward_list = q_table[(self._lower_pos, self._higher_pos)]
        action_list = self.get_available_actions()

        if ( (not ignore_epsilon) and (random.random() < self.epsilon) ): #Pick random action
            return random.choice(action_list)
        else: #Pick optimal choice
            max_reward = max(reward_list)
            action_candidates = []
            for action in action_list:
                if (reward_list[self.get_action_index(action)] >= max_reward):
                    action_candidates.append(action)
            return random.choice(action_list)
    
    def update_q_value(self, action_index:int, new_value:int) -> None:
        #Demeter will probably die reading this. Do not try to understand, just *flow* with it ;-;
        ((self._q_matrix[self._player_pos])[(self._lower_pos, self._higher_pos)])[action_index] = new_value
    
    def compute_error(self, r_matrix:dict[int,dict[tuple[int,int],list[int]]]) -> float:
        q_table = self._q_matrix[self._player_pos]
        r_table = r_matrix[self._player_pos]
        error = 0
        for position in q_table.keys():
            max_q = max(max(q_table[position]), 1)
            max_r = max(max(r_table[position]), 1)
            for value in zip(r_table[position], q_table[position]):
                if not( (value[0] == -1) and (value[1] == 0) ): #Only compute error for legal moves or 'legalized' illegal ones
                    error += abs((value[0]/max_r) - (value[1]/max_q))
        return error
    
    @performance_decorator
    #Simulate ghosts chasing Pacman for the desired number of episodes, updating own q-tables along the way. It is assumed that Pacman will not move
    def simulate_train(self, r_matrix:dict[int,dict[tuple[int,int],list[int]]], randomize_ghost_pos:bool, epsilon_delta:float, learn_rate:float, gamma:float, episode_count:int, max_steps:int = None, heartbeat_episode_freq:int = None, heartbeat_step_freq:int = None) -> list[float]:
        heartbeat_acc:list[int] = [0,0]
        start_epsilon = self.epsilon
        start_pos = self.ghost_pos
        error_list:list[float] = []

        for index in range(episode_count):
            if (randomize_ghost_pos):
                self.randomize_pos()
            else:
                self.update_self_pos(start_pos)

            step_count:int = 0
            heartbeat_acc[0] = 0
            while ( (self._lower_pos != self._player_pos) and (self._higher_pos != self._player_pos) ):
                action = self.pick_action()
                newPos_raw = self.parse_action(action)
                newPos = list(newPos_raw)
                newPos.sort()
                newPos = tuple(newPos)

                reward = r_matrix[self._player_pos][(self._lower_pos, self._higher_pos)][self.get_action_index(action)]
                maxFuture = max(r_matrix[self._player_pos][newPos])
                oldValue = self._q_matrix[self._player_pos][(self._lower_pos, self._higher_pos)][self.get_action_index(action)]
                newValue = oldValue + learn_rate * (reward + gamma*maxFuture - oldValue)

                self.update_q_value(self.get_action_index(action), round(newValue))
                self.update_self_pos(newPos)

                #Monitor performance
                step_count += 1
                heartbeat_acc[0] += 1
                if (heartbeat_step_freq is not None):
                    if (heartbeat_acc[0] >= heartbeat_step_freq):
                        heartbeat_acc[0] = 0
                        print(f"INFO. Step {step_count} of Episode {index+1} successful. Position: {self.ghost_pos}. Target: {self._player_pos}.")
                if (max_steps is not None):
                    if (step_count >= max_steps):
                        print("\033[93m" + f"WARN. Max steps hit for Episode {index+1}" + "\033[0m")
                        break
            #Update epsilon
            self.epsilon = (index+1 - episode_count)**2 * (epsilon_delta/(episode_count**2)) + (start_epsilon - epsilon_delta)
            #Monitor episode performance
            error = self.compute_error(r_matrix)
            error_list.append(round(error,6))
            heartbeat_acc[1] += 1
            if (heartbeat_episode_freq is not None):
                if (heartbeat_acc[1] >= heartbeat_episode_freq):
                    heartbeat_acc[1] = 0
                    print(f"INFO. Episode {index+1} successful. Epsilon: {round(self.epsilon,6)}. Error: {round(error,4)}.")
        self.update_self_pos(start_pos) #Restore previous position after simulation
        self.epsilon = start_epsilon #Restore previous epsilon
        return error_list


