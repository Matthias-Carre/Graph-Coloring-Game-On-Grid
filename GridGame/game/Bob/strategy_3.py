"""
This file contains the logic for Bob's strategy 3 in the GridGame.
This strategy is designed for a 3*n grid with 3 colors where Bob will win.
"""

def has_diagonal(grid, Alice_move):
    if len(grid.last_moves) <= 2:
        return False
    lx, ly, lc = grid.last_moves[-2]

    # Vérifier si le coup est en diagonale (par exemple, ly = 0 ou ly = 2)
    if ly == 0 or ly == 2:
        print("Bob strategy 3: has_diagonal True")
        return True

def solve_diagonal(grid, Alice_move):
    print("Solve diagonal")
    lx, ly, lc = grid.last_moves[-2]
    return (lx, 1, lc+1%3)

def is_side(grid, Alice_move):
    #check if Alice played on the side
    lx,ly,lc = Alice_move
    if(ly == 0 or ly == 2):
        print("Bob strategy 3: is_side True")
        return True

def solve_side(grid, Alice_move):
    print("Bob strategy 3: solve_side")
    lx,ly,lc = Alice_move   
    if(ly == 0):
        print("Bob strategy 3: solve_side 0")
        return (lx+1,2,lc)
    else:# (ly == 2):
        print("Bob strategy 3: solve_side 2")
        return (lx+1,0,lc)
    
    

def is_center(grid, Alice_move):
    #check if Alice played on the center
    lx,ly,lc = Alice_move
    if(ly == 1):
        print("Bob strategy 3: is_center True")
        return True

def solve_center(grid, Alice_move):
    print("Bob strategy 3: solve_center")
    lx,ly,lc = Alice_move
    return (lx+1,ly+1,lc+1) 

def has_color_critical(grid, Alice_move):
    
    #check if bob move is color critical
    lx,ly,lc = Alice_move
    print(f"Bob strategy 3 GET CELL {lx,ly} ")
    Alice_cell = grid.get_cell(lx,ly)
    print("check as color crit")
    for neighbor in Alice_cell.neighbors:
        if neighbor.is_color_critical:
            print("Bob strategy 3: as_color_critical True")
            return True
    
    for col in grid.nodes:
        for cell in col:
            if cell.is_color_critical:
                print("Bob strategy 3: as_color_critical True")
                return True

    return False

def winning_move(grid, Alice_move):
    #check if bob move is winning
    '''
    empty_cells = []
    lx,ly,lc = Alice_move
    print(f"Bob strategy 3 GET CELL {lx,ly} ")
    Alice_cell = grid.get_cell(lx,ly)
    for neighbor in Alice_cell.neighbors:
        if neighbor.is_color_critical:
            print("Bob strategy 3: winning_move")
            empty_cells = neighbor.get_empty_neighbors()
            lc = neighbor.color_options[0] if neighbor.color_options else 1
            return (empty_cells[0].y, empty_cells[0].x,lc) if empty_cells else None
    #print(f"Bob strategy 3:{empty_cells[0]} ")
    '''
    res = None
    for col in grid.nodes:
        for cell in col:
            if cell.is_color_critical:
                lc = cell.color_options[0] 
                for neighbor in cell.neighbors:
                    if neighbor.value == 0:
                        res = (neighbor.y, neighbor.x, lc)

    return res