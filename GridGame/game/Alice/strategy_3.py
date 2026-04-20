
# strategy for Alice with 3 colors in 3*3 grid
# return (x,y,color)


def is_any(grid,last_move):
    return True


def is_side(grid,last_move):
    print("TEST is_side")
    if last_move is None:
        return False
    ax, ay, _ = last_move
    print(f"Bob played at ({ax}, {ay})")
    if ay == 0 or ay == 2:
        print("Bob played on the side")
        return True
    return False

def solve_side(grid,last_move):
    ax, ay, acolor = last_move
    # play in the middle if possible
    cell = grid.get_cell(ax, 1)
    print(f"Alice check {cell} at ({ax}, {1})")
    if cell.value == 0:
        print(f"Alice plays at ({ax}, {1}) with color {cell.color_options[0]}")
        return (ax, 1, cell.color_options[0])
    else:
        return solve_other(grid,last_move)
    
def is_other(grid,last_move):
    return True

def solve_other(grid,last_move):
    print("TEST solve_other")
    for x in range(grid.width):
        if grid.get_cell(x, 1).value == 0:
            print(f"A")
            print(f"Alice plays at ({x}, {1}) with color {grid.get_cell(x, 1).color_options[0]}")
            return (x,1 , grid.get_cell(x, 1).color_options[0])
    
    if grid.empty_cells():
        x,y = grid.empty_cells()[0]
        print(f"Alice plays at ({x}, {y}) with color {grid.get_cell(x, y).color_options[0]}")
        
        return (x,y,grid.get_cell(x,y).color_options[0])
    
    print("Alice has no move to play")
    


def get_middle_free(grid):
    for x in range(grid.width):
        if grid.get_cell(x, 1).value == 0:
            return x
    return None