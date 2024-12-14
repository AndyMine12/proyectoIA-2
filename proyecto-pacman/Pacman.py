from GhostAI import GhostAI
from Agent_trainer import load_full_matrix, load_walls
from Performance_util import performance_decorator

QMATRIX_PATH = "output-files/ai-tables/GhostAI_Game.txt"

if __name__ == "__main__":
    qmatrix = load_full_matrix(QMATRIX_PATH, (18,9))
    ghost_brain = GhostAI((79,82,153), load_walls(), (18,9), qmatrix, 0)

    ghost_brain.simulate_game() #The game will be initialized regardless of initial state, since it resembles the original Pacman's setup