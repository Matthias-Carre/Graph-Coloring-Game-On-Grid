import random


def is_any(grid, bob_move):
    print("test any")
    return True

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
        