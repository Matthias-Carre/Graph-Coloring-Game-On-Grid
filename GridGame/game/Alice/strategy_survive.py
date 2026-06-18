import random

def is_any(grid, bob_move):
    print("test any")
    return True
        

#euristic
def eurisitic_move(grid, bob_move):
    # if a cell is color critical, then we play it
    # for the moment we play the color in the cell, maybe blocking it elsewhere is better
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if cell.check_color_critical():
            for color in cell.color_options:
                if grid.is_move_valid(x, y, color):
                    #print(f"euristic_move: playing color critical cell ({x}, {y}, {color})")
                    return (x, y, color)
    
    # if we can create 2 safe with one move:
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if cell.is_safe == False:
           for color in cell.color_options:
                future_safe_count = 0
                for neighbor in cell.neighbors:
                    if neighbor.value == 0 and color not in neighbor.color_options:
                        future_safe_count += 1
                if future_safe_count >= 2:
                    if grid.is_move_valid(x, y, color):
                        #print(f"euristic_move: creating 2 safe cells by playing ({x}, {y}, {color})")
                        return (x, y, color)
            
    # else play a move that dose not give oportunity to Bob to kill Alice
    # playing a cell with c where neighbor has allready c in neighbors
    
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        
        for color in cell.color_options:
            is_already_neighbor_color = True
            for neighbor in cell.neighbors:
                if neighbor.value == 0 and color in neighbor.color_options:
                    is_already_neighbor_color = False
            
            if is_already_neighbor_color:
                if grid.is_move_valid(x, y, color):
                    #print(f"euristic_move: playing cell ({x}, {y}, {color}) that does not give opportunity to Bob to kill Alice")
                    return (x, y, color)
    # and play c dose not create a cc cell
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        
        for color in cell.color_options:
            creates_cc = False
            for neighbor in cell.neighbors:            
                if neighbor.value == 0 and color in neighbor.color_options and len(neighbor.color_options)==2:
                    creates_cc = True
            if not creates_cc:
                if grid.is_move_valid(x, y, color):
                    #print(f"euristic_move: playing cell ({x}, {y}, {color}) that does not create a color critical cell")
                    return (x, y, color)
    print("euristic_move: no move found, playing survive strategy")                
    return survive_strategy(grid, bob_move)
    



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