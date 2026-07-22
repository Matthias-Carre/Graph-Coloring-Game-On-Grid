
# strategy for Alice with 3 colors in 3*3 grid
# return (x,y,color)

#test case
def is_any(grid,last_move):
    return True

#in : grid : grid of the game , bob_move : bob's last move (x,y,color)
#out : bool : True if the last move of Bob is on the side of the grid, False otherwise
# check if Bob played on the side of the grid (y=0 or y=2)
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

#in : grid : grid of the game , bob_move : bob's last move (x,y,color)
#out : (x,y,color) : Alice's next move
# if Bob played on the side, Alice will play in the middle of the same column if possible, otherwise she will play on the side
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

#Manage all remaining cases 
def is_other(grid,last_move):
    return True

#in : grid : grid of the game , bob_move : bob's last move (x,y,color)
#out : (x,y,color) : Alice's next move
# Alice try to play in the middle row if possible, otherwise she will play in the first free cell
def solve_other(grid,last_move):
    for x in range(grid.width):
        if grid.get_cell(x, 1).value == 0:
            print(f"Alice plays at ({x}, {1}) with color {grid.get_cell(x, 1).color_options[0]}")
            return (x,1 , grid.get_cell(x, 1).color_options[0])
    
    if grid.empty_cells():
        x,y = grid.empty_cells()[0]
        print(f"Alice plays at ({x}, {y}) with color {grid.get_cell(x, y).color_options[0]}")
        
        return (x,y,grid.get_cell(x,y).color_options[0])
    
    print("Alice has no move to play")
    

# in : grid : grid of the game 
# out : x : the x coordinate of a free cell in the middle row
# return the x coordinate of a free cell in the middle row, or None if there is no free cell in the middle row
def get_middle_free(grid):
    for x in range(grid.width):
        if grid.get_cell(x, 1).value == 0:
            return x
    return None