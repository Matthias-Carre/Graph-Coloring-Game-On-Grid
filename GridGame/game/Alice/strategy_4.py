"""
Every case of the paper
Note: in the paper line are from down to up starting from 1
Here we consider up to down starting from 0

"""


"""
in the normelized context we work with dx relative to j of the config 

get value of cell a,j+dx in a config:
color = get_norm_cell(grid,dx,a,j,is_h_flip,is_v_flip).value
used to get the color of a cell in the config


get real position of cell that would be a,j+x in the normalized context:
rx,ry = get_real_pos(grid,x,y,j,is_h_flip,is_v_flip)
used to know where Bob played and to translate Alice response
"""
#exemple de skelet de code pour l'exec
from matplotlib.pyplot import grid


def is_TestConfig(grid,bob_move):
    #C'est juste un exemple de test
    #if alpha Alice play diagonal same value (if possible)

    #if bob_move.config != "a":
    if "a" != "a":
        return False
    return True
    
def solve_TestConfig(grid,bob_move):
    lx,ly,lc = bob_move
    
    print("resolve test config")
    return (0,0,1)


#Bob joue dans j+1 ou j+2 de D 
# 1. Bob color sick => Alice color any j+1
# 2. Bob not color sick => Alice color sick with available color
def is_1Delta(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)

    if block.particular_config != "Delta":
        return False

    j = block.particular_config_j
    #Bob play in j+1 or j+2 of Delta
    print("x =",x,"j=",j)
    if x == j+1 or x == j+2:
        return True

    print("Bob in block D","j=",block.particular_config_j)
    return False

def solve_1Delta(grid,bob_move):
    x,y,color = bob_move
    j =  grid.blocks.block_at(x).particular_config_j
    
    if x == j+1 and y == 1 :
        print("Alice colore dans j+1 ")
    else:
        print("Alice colore sick")
        
def is_Delta_p_a(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)

    if block.particular_config != "Delta'":
        return False
    j = block.particular_config_j
    #Bob play in (1,j-1) or (0,j+1)
    print("DPA: Bob last move ",(x,y))
    print("DPA: check:",2,j-1,"or",1,j)
    print("Bob last move 2,j-1 ",(y,x) == (2,j-1), "or" "1,j",(y,x) == (1,j))
    print("j=",j)
    if ((y,x) == (2,j-1)) or ((y,x) == (1,j)):
        print("DELTRA P A")
        return True
    return False

def solve_Delta_p_a(grid,bob_move):

    print("Alice joue (2,j+1)")

def is_Delta_p_b(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)
    if block.particular_config != "Delta'":
        return False

    j = block.particular_config_j
    if ((y,x) == (2,j)):
        print("DELTRA P B")
        return True

def solve_Delta_p_b(grid,bob_move):
    
    print("Alice joue")
    
def is_Delta_p_c(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)
    if block.particular_config != "Delta'":
        return False
    j = block.particular_config_j

    if ((y,x) == (2,j+1)):
        print("DELTRA P C")
        return True

def solve_Delta_p_c(grid,bob_move):
    
    print("Alice joue")

def is_Delta_p_d(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)
    if block.particular_config != "Delta'":
        return False
    j = block.particular_config_j

    if ((y,x) == (1,j+2)):
        print("DELTRA P D")
        return True

def solve_Delta_p_d(grid,bob_move):
    
    print("Alice joue")

def is_Delta_p_e(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)

    if block.particular_config != "Delta'":
        return False
    j = block.particular_config_j
    if ((y,x) == (4,j+2)):
        print("DELTRA P E")
        return True
    
def solve_Delta_p_e(grid,bob_move):
    
    print("Alice joue")


def is_Delta_p_f(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)

    if block.particular_config != "Delta'":
        return False
    j = block.particular_config_j
    if ((y,x) == (2,j+2)):
        print("DELTRA P F")
        return True

def solve_Delta_p_f(grid,bob_move):
    
    print("Alice joue")

def is_Delta_p_2(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)

    if block.particular_config != "Delta2'":
        return False
    
    return True

#Bob play in (j-2,j-1 or j) in Lambda or Lambda2
def is_Lambda_a(grid,bob_move):
    # 4,j-1 -> 3,j-1
    return False


"""
Case 3: Bob colors empty column
"""

# Bob play in col j with j-1,j and j+1 empty 
def is_3_new(grid,bob_move):
    x,y,color = bob_move
    #previous and next column
    list = [(x-1,0),(x-1,1),(x-1,2),(x-1,3),(x+1,0),(x+1,1),(x+1,2),(x+1,3),(x,0),(x,1),(x,2),(x,3)]
    list.remove((x,y))
    if same_value_grid(grid,list):
        print("Case 3-new")
        return True
    return False

# Alice answer in col j with |a-b| = 2 with c
def solve_3_new(grid,bob_move):
    print("Case 3-new: Alice color v_b,j with |a-b| = 2 with c")
    x,y,color = bob_move
    if y == 0 or y == 1:
        return (x,y+2,color)
    elif y == 2 or y == 3:
        return (x,y-2,color)


def is_3_pi(grid,bob_move):
    if grid.bob_play_on_config["config"] == "p":
        print("Is 3 pi")
        return True
    return False

def solve_3_pi(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    

    #fix j is full line of 3_pi is right or left
    j = x+1 if is_v_flip else x-1 

    #bob 2,j+1 => alice 1,j+1

    #print("3Pi: Bob last move ",(x,y))
    #print("3Pi: in :",grid.bob_play_on_config["config"])
    #print("3Pi: Bob normalized move: ",get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip))
    #print("3Pi: check j+2, 2:",get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip).value)
    #print("3Pi: flip h and v: ",is_h_flip, is_v_flip)
    dx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    if(ny == 2):
        col = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip).color_options
        #print("3Pi color option: ", col)
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        #print("3Pi real pos: ",rx,ry)
        print(f"3Pi: 1")
        return (rx,ry,col[0])
    if(ny == 1):
        col = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip).color_options
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print(f"3Pi: 2")
        return (rx,ry,col[0])
    
    #bob 3,j+1 cw c' or c'' => alice 1,j+1 cw available 
    if(ny == 3):
        #cell c'
        col_cell_1 = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
        #cell c''
        col_cell_2 = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
        #color v3,j+1 w c' or c''
        if color == col_cell_1.value or color == col_cell_2.value:
            c = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip).color_options
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            print(f"3Pi: 3")
            return (rx,ry,c[0])
        #bob 3,j+1 cw w => if 1,j+2 != w => alice 1,j+1 cw w else 1,j+1 cw c''
        if color != get_norm_cell(grid,dx+1,1,j,is_h_flip,is_v_flip).value:
            rx,ry = get_real_pos(grid,dx,1,j,is_h_flip,is_v_flip)
            print(f"3Pi: 4")
            return (rx,ry,color)
        else:
            #get the value of c'' (j,2)
            cell = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)

            print(f"3Pi: 5")
            return (rx,ry,cell.value)

    if (ny == 0):
        #if 0,j+1 = c' => 2,j+1 available 
        c1 = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
        if color == c1.value:
            col = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip).color_options
            rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
            print(f"3Pi: 6")
            return (rx,ry,col[0])
        
        #if 0,j+1 =  w => 2,j+1 w
        c = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
        c2 = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)

        #calc of w
        possi = [1,2,3,4]
        possi.remove(c.value)
        possi.remove(c1.value)
        possi.remove(c2.value)
        w = possi[0]

        print(f"3Pi: c={c.value}, c'={c1.value}, c''={c2.value},w={w}")
        if color == w:
            print(f"3Pi: 7")
            rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
            return (rx,ry,color)
        
        #if 0,j+1 = c'' => if 1,j+2 c'' => 2,j+1 aviable
        if color == c2.value:
            cell_1_jp2 = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
            if cell_1_jp2.value == c2.value:
                col = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip).color_options
                rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
                print(f"3Pi: 8")
                return (rx,ry,col[0])

            #if 0,j+1 = c'' => if 1,j+2 c or w => 2,j+1 same
            if cell_1_jp2.value == c.value or cell_1_jp2.value == w:
                rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
                print(f"3Pi: 9")
                return (rx,ry,color)

            #if 0,j+1 = c' => if 1,j+2 0 => 1,j+1 w
            if cell_1_jp2.value == 0:
                rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
                print(f"3Pi: 10")
                return (rx,ry,w)
        
    print("3Pi: no condition matched")  
    return
        

"""
    
    print("strat: ",color, grid.get_cell(x,1).value, grid.get_cell(x,2).value)
    if y == 3:
        if color == grid.get_cell(x-1,2).value or color == grid.get_cell(x+1,2).value:
            c = grid.get_cell(x,1).color_options
            #print("3Pi color option: ", c)
            return (x,1,c[0])
        
        #bob 3,j+1 cw w => if 1,j+2 != w => alice 1,j+1 cw w else 1,j+1 cw c''
        if color != grid.get_cell(x+1,1).value:
            return (x,1,color)
        else:
            #get the value of c''

            return (x,1,grid.get_cell(x-1,2).value)

    return
"""

def is_3_delta(grid,bob_move):
    #bob coor in col adjacent to border of config delta
    #idea: Alice will color to obtain alpha beta gamma or delta or merge
    print("Check 3 delta: ", grid.bob_play_on_config)
    if grid.bob_play_on_config["config"] == "d":
        print("Is 3 delta")
        return True
    
    return False

def solve_3_delta(grid,bob_move):

    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    
    #fix j
    print(f"3Delta: Bob last move{(x,y)},{is_h_flip},{is_v_flip} ",) 
    j = x+1 if is_v_flip else x-1
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #Case 3d1
    #bob 3,j+1 y if 1,j+2 != y => alice 1,j+1 w y
    if(ny == 3):
        cell_2_j = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
        if color == cell_2_j.value:
            cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
            if cell_1_jp2.value != color:
                rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
                print("3Delta: Case 3d1a")
                return (rx,ry,color)
            else:
                #if 1,j+2 = y => alice 1,j+1 w y
                rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
                print("3Delta: Case 3d1b")
                return (rx,ry,color)
    #Case 3d2
    #bob 3,j+1 c != y => alice 1,j+1 c or y
        else: #color != y
            cell = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
            cell_y = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
            print(f"3Delta: j={j}")

            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            #if y is an option for 1,j+1
            print(f"y={cell_y.value}, options 1,j+1: {cell.color_options},c={color}")
            if cell_y.value in cell.color_options:
                print("3Delta: Case 3d2a")
                return (rx,ry,cell_y.value)
            #else (y not an option) => color c
            else:
                rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
                print("3Delta: Case 3d2b")
                return (rx,ry,color)
            
    #Case 3d3
    #bob 2,j+1 c = y if j+2 not empty => alice 1,j+1 available
    if(ny == 2):
        cell_y = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
        if color != cell_y.value:
            #check if j+2 not empty
            print(f"3Delta: Is j+2 empty: {is_column_empty(grid,2,j,is_v_flip)}")
            if not is_column_empty(grid,2,j,is_v_flip):
                cell = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
                rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
                print("3Delta: Case 3d3a1")
                return (rx,ry,cell.color_options[0])
    #bob 2,j+1 c != y if j+2 empty if 1,j+3 != c => alice 1,j+2 c else 0,j+2 c
            else: #j+2 empty
                cell_1_jp3 = get_norm_cell(grid,3,1,j,is_h_flip,is_v_flip)
                if cell_1_jp3.value != color:
                    rx,ry = get_real_pos(grid,2,1,j,is_h_flip,is_v_flip)
                    print("3Delta: Case 3d3a2")
                    return (rx,ry,color)
                else:
                    rx,ry = get_real_pos(grid,2,0,j,is_h_flip,is_v_flip)
                    print("3Delta: Case 3d3b")
                    return (rx,ry,color)

    #case 3d4
    #bob 1,j+1 c if j+2 not empty => alice 2,j+1 available
    if(ny == 1):
        if not(is_column_empty(grid,2,j,is_v_flip)):
            cell = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
            rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
            print("3Delta: Case 3d4a")
            return (rx,ry,cell.color_options[0])
    #bob 1,j+1 c if j+2 empty 3,j+1 y
        else:
            cell_y = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
            rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
            print(f"3Delta: Case 3d4b")
            return (rx,ry,cell_y.value)

    #case 3d5
    #bob 0,j+1 c != x if c != y and 1,j+2 != y => alice 1,j+1 y 
    if(ny == 0):
        cell_y = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
        if color != cell_y.value:
            cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
            if cell_1_jp2.value != cell_y.value:
                rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
                print("3Delta: Case 3d5a")
                return (rx,ry,cell_y.value)
            
            else:# 1,j+2 = y => alice 1,j c
                rx,ry = get_real_pos(grid,0,1,j,is_h_flip,is_v_flip)
                print("3Delta: Case 3d5b")
                return (rx,ry,color)
        #if color = y if 3,j+2 != y => alice 3,j+1 y else if...
        else: #color = y
            cell_3_jp2 = get_norm_cell(grid,2,3,j,is_h_flip,is_v_flip)
            if cell_3_jp2.value != cell_y.value:
                rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
                print("3Delta: Case 3d5c")
                return (rx,ry,cell_y.value)
            #if c=y and 3,j+2 = y if 2,j+2 = c' != 0 => alice 1,j+1 c' else 
            #- if 1,j+2 = c' => alice 2,j+1 c' (if c' != y or other) else(1,j+2=0) should not be possible
            else: # 3,j+2 = y
                cell_2_jp2 = get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip)
                if cell_2_jp2.value != 0:
                    rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
                    print("3Delta: Case 3d5d")
                    return (rx,ry,cell_2_jp2.value)
                else: # 2,j+2 = 0
                    cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
                    if cell_1_jp2.value != 0: 
                        if cell_y.value != cell_1_jp2.value:
                            rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
                            print("3Delta: Case 3d5e")
                            return (rx,ry,cell_1_jp2.value)
                        else:
                            cell = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
                            rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
                            print("3Delta: Case 3d5f")
                            return (rx,ry,cell.color_options[0])

                    else: # 1,j+2 = 0
                        print("3Delta: Case 3d5f - should not happen")

    print("3Delta: no condition matched")
    return


def is_3_alpha_F(grid,bob_move):
    #Bob play border of alpha with no block on the other side
    if grid.bob_play_on_config["config"] == "a":
        if grid.bob_play_on_config["config2"] == "empty":
            print("Is 3 alpha F")
            return True 
    return False

def solve_3_alpha_F(grid,bob_move):
    
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    
    j = x+1 if is_v_flip else x-1
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #Bob play in 3,j+1 or 0,j+1 => Alice play in 2,j+1 c
    if (ny == 3 or ny == 0):
        cell_c = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("3Alpha F1") 
        return (rx,ry,cell_c.value)
    #if Bob 1,j+1 c' => Alice 3,j+1 c'
    if (ny == 1):
        rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
        print("3Alpha F2")
        return (rx,ry,color)
    #if Bob play 2,j+1 c' => Alice play 0,j+1 c
    if (ny == 2):
        cell_c = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
        print("3Alpha F3")
        return (rx,ry,cell_c.value)
    
    print("3Alpha F: no condition matched")
    return

def is_3_beta_F(grid,bob_move):
    #Bob play border of beta with no block on the other side
    if grid.bob_play_on_config["config"] == "b":
        if grid.bob_play_on_config["config2"] == "empty":
            print("Is 3 beta F")
            return True 
    return False

def solve_3_beta_F(grid,bob_move):

    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    
    j = x+1 if is_v_flip else x-1
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #Bob play 3,j+1 c' if != c => Alice 1,j+1 c' else 0,j+1 c
    if (ny == 3):
        cell_c = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
        if color != cell_c.value:
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            print("3Beta F1")
            return (rx,ry,color)
        else:
            rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
            print("3Beta F2")
            return (rx,ry,cell_c.value)
    #Bob play 2,j+1 c' => Alice play 0,j+1 c
    if (ny == 2):
        cell_c = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
        print("3Beta F3")
        return (rx,ry,cell_c.value)
    #Bob play 0,j+1 c' => Alice 2,j+1 c
    if (ny == 0):
        cell_c = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("3Beta F4")
        return (rx,ry,cell_c.value)
    #Bob play 1,j+1 c' => if 3,j != c' => Alice 3,j+1 c' else (if 2,j+3 != c' => Alice 2,j+2 c' else Alice 3,j+2 c')
    if (ny == 1):
        cell_3_j = get_norm_cell(grid,0,3,j,is_h_flip,is_v_flip)
        if color != cell_3_j.value:
            rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
            print("3Beta F5")
            return (rx,ry,color)
        else:
            cell_2_jp3 = get_norm_cell(grid,3,2,j,is_h_flip,is_v_flip)
            if color != cell_2_jp3.value:
                rx,ry = get_real_pos(grid,2,2,j,is_h_flip,is_v_flip)
                print("3Beta F6")
                return (rx,ry,color)
            else:
                rx,ry = get_real_pos(grid,2,3,j,is_h_flip,is_v_flip)
                print("3Beta F7")
                return (rx,ry,color)
            
    print("3Beta F: no condition matched")
    return


def is_3_gamma_F(grid,bob_move):
    #Bob play border of gamma with no block on the other side
    if grid.bob_play_on_config["config"] == "g":
        if grid.bob_play_on_config["config2"] == "empty":
            print("Is 3 gamma F")
            return True 
    return False

def solve_3_gamma_F(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = x+1 if is_v_flip else x-1
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #bob play 0,j+1 c' => Alice 2,j+1 c'
    if (ny == 0):
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("3Gamma F1")
        return (rx,ry,color)
    
    #bob play 3,j+1 c' => Alice 1,j+1 c'
    if (ny == 3):
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("3Gamma F2")
        return (rx,ry,color)
    #bob play 2,j+1 c' != c => Alice 1,j c'
    if (ny == 2):
        cell_c = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
        if color != cell_c.value:
            rx,ry = get_real_pos(grid,0,1,j,is_h_flip,is_v_flip)
            print("3Gamma F3")
            return (rx,ry,color)
    #bob play 2,j+1 c' = c => if 1,j+3 != c => Alice 1,j c else if 3,j+3 != c => Alice 0,j+2 c
        else:
            cell_1_jp3 = get_norm_cell(grid,3,1,j,is_h_flip,is_v_flip)
            if cell_c.value != cell_1_jp3.value:
                rx,ry = get_real_pos(grid,0,1,j,is_h_flip,is_v_flip)
                print("3Gamma F4")
                return (rx,ry,cell_c.value)
            else:
                cell_3_jp3 = get_norm_cell(grid,3,3,j,is_h_flip,is_v_flip)
                if cell_c.value != cell_3_jp3.value:
                    rx,ry = get_real_pos(grid,2,0,j,is_h_flip,is_v_flip)
                    print("3Gamma F5")
                    return (rx,ry,cell_c.value)

    #bob play 1,j+1 c' != c => Alice 2,j c'
    if (ny == 1):
        cell_c = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
        if color != cell_c.value:
            rx,ry = get_real_pos(grid,0,2,j,is_h_flip,is_v_flip)
            print("3Gamma F6")
            return (rx,ry,color)
    #bob play 1,j+1 c' = c if 2,j+3 != c => Alice 2,j+2 c else we are in Delta'
        else:
            cell_2_jp3 = get_norm_cell(grid,3,2,j,is_h_flip,is_v_flip)
            if color != cell_2_jp3.value:
                rx,ry = get_real_pos(grid,2,2,j,is_h_flip,is_v_flip)
                print("3Gamma F7")
                return (rx,ry,color)
            else:
                rx,ry = get_real_pos(grid,2,3,j,is_h_flip,is_v_flip)
                print("3Gamma F8 *2TH:je supp a verifier")
                return (rx,ry,color)
    print("3Gamma F: no condition matched")
    return

def is_3_gamma(grid,bob_move):
    #Bob play between gamma and (alpha beta or gamma)
    
    return False
    

"""
input: list of (j,x) coordinates
return true if all the cells in the list have the same value
"""
def same_value_grid(grid,list):
    (j,y) = list[0]
    first_value = grid.get_cell(j,y).value
    for j,y in list: 
        if grid.get_cell(j,y).value != first_value: 
            return False
    return True

"""ckeck if column j is empty from normized context """
def is_column_empty(grid,dx,j,verti):
    rj = j-dx if verti else j+dx

    for y in range(grid.height):
        if grid.get_cell(rj,y).value != 0:
            return False
    return True


"""
input: grid, dx, y, j, is_hori_flipped, is_vert_flipped
    dx is just the position relative to j
return: the cell at (x,y) on this context

"""
def get_norm_cell(grid,dx,y,j,hori,verti):

    if hori and verti:
        print("strategy: dx,y,j , nx,ny ",dx,y,j,2*j-dx,grid.height-1-y)
        return grid.get_cell(j-dx,grid.height-1-y)
    elif hori:
        return grid.get_cell(j+dx,grid.height-1-y)
    elif verti:
        return grid.get_cell(j-dx,y)
    else:
        return grid.get_cell(j+dx,y)

"""
input: grid, x, y, j, is_hori_flipped, is_verti_flipped
return: the coordinates of (x,y) on the normalized context
x will be the position relative to j
idea: bob move is translate to his position after normalization
"""
def get_norm_pos(grid,x,y,j,hori,verti):
    dx_norm = j-x if verti else x-j
    y_norm = grid.height-1-y if hori else y 

    return (dx_norm,y_norm)

"""
input: grid, x, y, j, is_hori_flipped, is_verti_flipped
output: the coordinates of (x,y) in the real grid
"""
def get_real_pos(grid,dx,y,j,hori,verti):
    x_real = j - dx if verti else j+dx
    y_real = grid.height-1-y if hori else y 

    return (x_real,y_real)