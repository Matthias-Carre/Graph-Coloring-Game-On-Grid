"""
This file contains the logic for Alice's survive strategy in the GridGame.
It's an heuristic strategy that allows Alice to play the game without losing, by avoiding moves that would lead to a loss.
"""
import random

def is_any(grid, bob_move):
    print("test any")
    return True

DEBUG = False



#heuristic

# in : grid : grid of the game , bob_move : bob's last move (x,y,color)
# out : (x,y,color) : Alice's next move
# heuristic for Alice:
# 1. if a cell is color critical, then we play it
# 2. else if cc we play the neighbor of the cc cell that does not create a cc cell
# 3. else if we can create 2 safe with one move,
# 4. else play a move that dose not give oportunity to Bob to kill Alice
def heurisitic_move(grid, bob_move):

    # if a cell is color critical, then we play it
    # for the moment we play the color in the cell, maybe blocking it elsewhere is better
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if cell.check_color_critical():
            
            for color in cell.color_options:
                if grid.is_move_valid(x, y, color) and not is_move_creating_cc(grid, x, y, color):
                    
                    if DEBUG:
                        print(f"euristic_move: playing color critical cell ({x}, {y}, {color})")
                    return (x, y, color)
            
            # here its mean that we can not plays the cell in the middle
            #print("CC cell not managed")
            
            
    # else if cc we play the neighbor of the cc cell that does not create a cc cell
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if cell.check_color_critical():
            for neighbor_cell in cell.neighbors:
                if neighbor_cell.value == 0:
                    n_x, n_y = neighbor_cell.y, neighbor_cell.x
                    
                    for color in neighbor_cell.color_options:

                        if not is_move_creating_cc(grid, n_x, n_y, color) and grid.is_move_valid(n_x, n_y, color):
                        
                            if DEBUG:
                                print(f"euristic_move: playing neighbor of color critical cell ({neighbor_cell.x}, {neighbor_cell.y}, {color})")
                            return (n_x, n_y, color)
            
            #print("problem euristic_move: color critical cell not managed")
            
        
        
        
    # if we can create 2 safe with one move:
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if cell.is_safe == False:
           for color in cell.color_options:
                future_safe_count = 0
                for neighbor in cell.neighbors:
                    if neighbor.value == 0 and color not in neighbor.color_options and neighbor.number_of_neighbors() == 4:
                        future_safe_count += 1
                if future_safe_count >= 2:
                    #print(f"euristic_move: 2safe: {is_move_creating_cc(grid, x, y, color)}")
                    if grid.is_move_valid(x, y, color) and not is_move_creating_cc(grid, x, y, color):
                        if DEBUG:
                            print(f"euristic_move: creating 2 safe cells by playing ({x}, {y}, {color})")
                        return (x, y, color)
            
    # else play a move that dose not give oportunity to Bob to kill Alice

                
    # play to create 1 safe cell
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)

        for color in cell.color_options:
            future_safe_count = 0
            for neighbor in cell.neighbors:
                if neighbor.value == 0 and color not in neighbor.color_options and neighbor.number_of_neighbors() == 4:
                    future_safe_count += 1
            if future_safe_count >= 1:
                if grid.is_move_valid(x, y, color) and not is_move_creating_cc(grid, x, y, color):
                    if DEBUG:
                        print(f"euristic_move: creating 1 safe cell by playing ({x}, {y}, {color})")
                    return (x, y, color)
            
    # playing a cell with c where neighbor has allready c in neighbors
    
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        
        for color in cell.color_options:
            is_already_neighbor_color = True
            for neighbor in cell.neighbors:
                if neighbor.value == 0 and color in neighbor.color_options:
                    is_already_neighbor_color = False
            
            if is_already_neighbor_color:
                if grid.is_move_valid(x, y, color) and not is_move_creating_cc(grid, x, y, color):
                    if DEBUG:
                        print(f"euristic_move: playing cell ({x}, {y}, {color}) that does not give opportunity to Bob to kill Alice")
                    return (x, y, color)
    
    # and play c dose not create a cc cell
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        
        for color in cell.color_options:
            creates_cc = False
            for neighbor in cell.neighbors:            
                if neighbor.value == 0 and color in neighbor.color_options and len(neighbor.color_options)<=2:
                    creates_cc = True
            if not creates_cc:
                if grid.is_move_valid(x, y, color) and not is_move_creating_cc(grid, x, y, color):
                    if DEBUG:
                        print(f"euristic_move: playing cell ({x}, {y}, {color}) that does not create a color critical cell")
                    return (x, y, color)
    #print("euristic_move: no move found, playing survive strategy")
    return survive_strategy(grid, bob_move)
    


# in : grid : grid of the game , bob_move : bob's last move (x,y,color)
# out : bool : True if the move (x,y,c) creates a color critical cell, False otherwise
# check if the move (x,y,c) creates a color critical cell
def is_move_creating_cc(grid, x,y,c):
    #print(f"checking if move ({x}, {y}, {c}) creates a color critical cell")
    cell = grid.get_cell(x, y)
    for neighbor in cell.neighbors:
        #print(f"val: {neighbor.value}, safe: {neighbor.is_safe}, num_neighbors: {neighbor.number_of_neighbors()}, color_options: {neighbor.color_options}")
        if neighbor.value == 0 and not(neighbor.is_safe) and neighbor.number_of_neighbors() == 4 and c in neighbor.color_options and len(neighbor.color_options)<=2:
            return True
    if grid.is_move_kill_alice(x, y, c):
        return True
    return False
    


#in : grid : grid of the game , bob_move : bob's last move (x,y,color)
#out : (x,y,color) : Alice's next move
# Alice try to play a random safe move if possible, otherwise she will play a random legal move
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