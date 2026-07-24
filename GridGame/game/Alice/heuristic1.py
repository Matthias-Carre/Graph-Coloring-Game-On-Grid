import random


#Heuristic for Alice
#Take the grid and output a move (x,y,color) for Alice


# Any case
def is_any(grid, bob_move):
    print("test any")
    return True

#in : grid : grid of the game , bob_move : bob's last move (x,y,color)
#out : (x,y,color) : Alice's next move
# Check for color critical cells and play them if they exist.
def critical_strategy(grid, bob_move):
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if cell.check_color_critical():
            for color in cell.color_options:
                if grid.is_move_valid(x, y, color):
                    return (x, y, color)
    return play_same_in_diag(grid, bob_move)

#in : grid : grid of the game , bob_move : bob's last move (x,y,color)
#out : (x,y,color) : Alice's next move
#try to play the same color as Bob in diagonal cells if possible, otherwise play a safe move
def play_same_in_diag(grid, bob_move):
    if bob_move is None:
        return (1,1,1)
    x, y, color = bob_move
    diag = [(x-1, y-1), (x+1, y+1), (x-1, y+1), (x+1, y-1)]
    for a_x, a_y in diag:
        if grid.is_move_valid(a_x, a_y, color):
            return (a_x, a_y, color)
    return survive_strategy(grid, bob_move)

#in : grid : grid of the game , bob_move : bob's last move (x,y,color)
#out : (x,y,color) : Alice's next move
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