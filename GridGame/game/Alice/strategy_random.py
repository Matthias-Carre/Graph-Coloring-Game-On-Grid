import random

#Logic for Alice to play a random move


#test case to return True for any grid and any last move of Bob
def is_any(grid, bob_move):
    print("test any")
    return True


# in : grid : grid of the game , bob_move : bob's last move (x,y,color)
# out : (x,y,color) : Alice's next move
# return a random valid move (x,y,color) for Alice, None if there is no valid move
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
        