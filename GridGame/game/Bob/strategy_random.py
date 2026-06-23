import random


def is_any(grid, bob_move):
    return True


# check for cc, play it
# check for cell with 2 colors option and 2 empty neighbors.
# check for non safe cell and play beside it
# random move if no other option
import random


def euristic_move(grid, bob_move):

    # Collect all valid moves for cc cell heuristic
    valid_cc_moves = []
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if len(cell.color_options) == 1:
            c = cell.color_options[0]
            # Retrieve the uncolored neighbor of the cc cell
            res = cell.get_uncolored_neighbor()
            if res is not None and c in res.color_options:
                valid_cc_moves.append((res.y, res.x, c))
                
    if valid_cc_moves:
        return random.choice(valid_cc_moves)
    

    #check if exist a cell where you can create 2 cc cell beside it 
    #print(f"empty cells: {list(grid.empty_cells())}")
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if len(cell.color_options) == 2 and cell.number_of_neighbors() == 4:
            #print(f"cell with 2 color options and 4 neighbors : ({cell.y}, {cell.x})")
            empty_neighbors = cell.get_empty_neighbors()
            for neighbor in empty_neighbors:
                neighbors_2 = neighbor.get_empty_neighbors()
                for neighbor_2 in neighbors_2:
                    # Ensure it's not the original cell
                    if neighbor_2.number_of_neighbors() == 4 and len(neighbor_2.color_options) == 2 and (neighbor_2.x != cell.x or neighbor_2.y != cell.y):
                        
                        # "neighbor" as 2 neighbors with only 2 color options
                        # if existe same color for those 2 we use it
                        #print(f"TEST n1: ({cell.color_options}, {neighbor_2.color_options})")
                        colors = set(cell.color_options).intersection(set(neighbor_2.color_options))
                        #print(f"TEST color: {colors}")  
                        if colors:
                            return neighbor.y, neighbor.x, colors.pop()  # Return the first color from the intersection         


    # Collect all valid moves for cells with exactly 2 color options
    valid_two_colors_moves = []
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if len(cell.color_options) == 2:
            colors = cell.color_options
            res = cell.get_uncolored_neighbor()
            if cell.number_of_neighbors() == 4 and res is not None:
                if colors[0] in res.color_options:
                    valid_two_colors_moves.append((res.y, res.x, colors[0]))
                elif colors[1] in res.color_options:
                    valid_two_colors_moves.append((res.y, res.x, colors[1]))
                    
    if valid_two_colors_moves:
        return random.choice(valid_two_colors_moves)

    # Collect all valid moves around non-safe cells
    valid_non_safe_moves = []
    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        if not cell.is_safe:
            colors = cell.color_options
            res = cell.get_uncolored_neighbor()
            if res is not None and cell.number_of_neighbors() == 4:
                # pick random color:
                chosen_color = random.choice(colors)
                if chosen_color in res.color_options:
                    valid_non_safe_moves.append((res.y, res.x, chosen_color))
                if colors[0] in res.color_options:
                    valid_non_safe_moves.append((res.y, res.x, colors[0]))
                elif len(colors) > 1 and colors[1] in res.color_options:
                    valid_non_safe_moves.append((res.y, res.x, colors[1]))
                elif len(colors) > 2 and colors[2] in res.color_options:
                    valid_non_safe_moves.append((res.y, res.x, colors[2]))
                    
    if valid_non_safe_moves:
        return random.choice(valid_non_safe_moves)

    # Fallback to pure random move if no heuristics matched
    return random_move(grid, bob_move)




# return a move that wins if possible, otherwise return a possible move to try to create a winning condition in the next move
def little_smart_bob(grid, bob_move):
    
    #check for cc cell
    for x,y in grid.empty_cells():
        cell = grid.get_cell(x,y)
        if len(cell.color_options) == 1:
            c = cell.color_options[0]
            #get the uncolored neighbor of the cc cell
            res = cell.get_uncolored_neighbor()
            if res is not None and c in res.color_options:
                return res.y, res.x, c
    #check for cell with only 2 color options


    for x,y in grid.empty_cells():
        cell = grid.get_cell(x,y)
        if len(cell.color_options) == 2:
            colors = cell.color_options
            res = cell.get_uncolored_neighbor()
            if res is not None:
                
                if colors[0] in res.color_options:
                    return res.y, res.x, colors[0]
                elif colors[1] in res.color_options:
                    return res.y, res.x, colors[1]

    #else return random for now
    return random_move(grid, bob_move)

def kill_if_possible(grid, bob_move):
    for x,y in grid.empty_cells():
        cell = grid.get_cell(x,y)
        if len(cell.color_options) == 1:
            c = cell.color_options[0]
            #get the uncolored neighbor of the cc cell
            res = cell.get_uncolored_neighbor()
            if res is not None and c in res.color_options:
                return res.y, res.x, c
    return random_move(grid, bob_move)


# Bob plays a random legal move.
def random_move(grid, bob_move):
    legal_moves = []

    for x, y in grid.empty_cells():
        cell = grid.get_cell(x, y)
        for color in cell.color_options:
            if grid.is_move_valid(x, y, color):
                legal_moves.append((x, y, color))

    if not legal_moves:
        return None

    return random.choice(legal_moves)
        