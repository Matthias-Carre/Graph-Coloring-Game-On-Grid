import random

def is_any(grid, bob_move):
    print("test any")
    return True
        

# Alice will never play a move that kill her unless there is no other choice. 
def survive_strategy(grid, bob_move):
    legal_moves = []
    safe_moves = []

    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        for color in cell.color_options:
            if grid.is_move_valid(x, y, color):
                legal_moves.append((x, y, color))
                if not(grid.is_move_kill_alice(x, y, color)):
                    safe_moves.append((x, y, color))
                

    if safe_moves:
        return random.choice(safe_moves)
    if legal_moves:
        #print("No safe move, playing legal move")
        return random.choice(legal_moves)
    return None