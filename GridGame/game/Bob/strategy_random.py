import random


def is_any(grid, bob_move):
    return True

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
        