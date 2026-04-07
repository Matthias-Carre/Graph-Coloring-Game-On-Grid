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
from logging import config

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
    print("No case matched")
    return (0,0,1)



#TEST FUNCTIOn
def is_TEST(grid,bob_move):
    return True

def solve_TEST(grid,bob_move):
    print("Strategy TEST: 1st gamma:",grid.get_first_gamma())
    print("Strategy TEST: 1st delta:",grid.get_first_border_delta())
    print("Strategy TEST: 1st pi:",grid.get_first_pi())
    print("Strategy TEST: 1st alpha:",grid.get_first_alpha())
    print("Strategy TEST: 1st beta:",grid.get_first_beta())
'''
Case 1
-------------##-------
-----------####-------
---------##--##-------
-------##----##-------
-------------##-------
-------------##-------
-------------##-------
-------------##-------
-------------##-------
Bob play:
    - in border D
    - in col j or j-1 of L or L2 or L' or L'2
    - in col j-2 of L or L'
    - in col j-2 of L2 or L'2 if j-3 is not empty
    - inside a block
'''
#Bob joue dans j+1 ou j+2 de D 
# 1. Bob color sick => Alice color any j+1
# 2. Bob not color sick => Alice color sick with available color
def is_1_Delta(grid,bob_move):
    x,y,color = bob_move

    if grid.bob_play_on_config["config"] != "D":
        return False
    print("Strat 1Delta: Bob played on:",grid.bob_play_on_config)
    return True

def solve_1_Delta(grid,bob_move):
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    
    j = grid.bob_play_on_config["j"]
    dx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #Bob play 1,j+1 => Alice play any of j+1
    #else => A 1,j+1
    if (dx == 1 and ny == 1):
        #Alice play 1,j+1 with any color
        cell = get_norm_cell(grid,1,0,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
        print("1 Delta a")
        return (rx,ry,cell.color_options[0])
    else:
        #Alice play 1,j+1 (color the sound vertex)
        cell = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("1 Delta b")
        return (rx,ry,cell.color_options[0])
    
def is_1_Dp_1(grid,bob_move):
    x,y,color = bob_move
    if grid.bob_play_on_config["config"] == "D'" :
        return True
    return False

#Bob play in in Delta'
def solve_1_Dp_1(grid,bob_move):
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = grid.bob_play_on_config["j"]

    dx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #Bob 2,j-1 or 1,j c => Alice 2,j+1 c
    print("1 Dp 1: Bob played on:",x,y ,"norm pos: ",dx,ny)
    if (dx == -1 and ny == 2) or (dx == 0 and ny == 1) :
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("1 Dp 1 a")
        return (rx,ry,color)
    #Bob 2,j c => Alice 3,j+1 c
    if (dx == 0 and ny == 2):
        rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
        print("1 Dp 1 b")
        return (rx,ry,color)
    
    #Bob 2,j+1 respc 3,j+1 => Alice 3,j+1 respc 2,j+1 available
    if (dx == 1 and ny == 2):
        cell = get_norm_cell(grid,1,3,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
        print("1 Dp 1 c1")
        return (rx,ry,cell.color_options[0])
    if (dx == 1 and ny == 3):
        cell = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("1 Dp 1 c2")
        return (rx,ry,cell.color_options[0])
    
    #Bob 1,j+2 => Alice 2,j+1 aviable
    if (dx == 2 and ny == 1):
        cell = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("1 Dp 1 d")
        return (rx,ry,cell.color_options[0])
    
    #Bob 0,j+2 or 0,j+1 => Alice 1,j+2 available
    if (dx == 2 and ny == 0) or (dx == 1 and ny == 0):
        cell = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,2,1,j,is_h_flip,is_v_flip)
        print("1 Dp 1 e")
        return (rx,ry,cell.color_options[0])

    #Bob 2,j+2 c' != c => Alice 1,j+2
    if (dx == 2 and ny == 2):
        cell_c = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
        if color != cell_c.value:
            cell = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
            rx,ry = get_real_pos(grid,2,1,j,is_h_flip,is_v_flip)
            print("1 Dp 1 f")
            return (rx,ry,cell.color_options[0])
        
    print("1 Dp 1 no condition matched ")
    return

def is_1_Dp_2(grid,bob_move):
    x,y,color = bob_move
    if grid.bob_play_on_config["config"] == "D2'":
        return True
    return False

def solve_1_Dp_2(grid,bob_move):
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = grid.bob_play_on_config["j"]

    dx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #If after Bob move, 2,j can be c' => Alice (1,j) c'
    
    #cell c' 
    cell_cp = get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip)
    #cell 2,j
    cell_2_j = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)

    if cell_2_j.value == 0 and (cell_cp.value in cell_2_j.color_options):
        rx,ry = get_real_pos(grid,0,1,j,is_h_flip,is_v_flip)
        print("1 Dp 2 a")
        return (rx,ry,cell_cp.value)
    
    #else A => 3,j+1 c'
    else:
        rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
        print("1 Dp 2 b")
        return (rx,ry,cell_cp.value)
    
    #Impossible Mais tql
    print("1 Dp 2 no condition matched")
    return

def is_1_L(grid,bob_move):
    x,y,color = bob_move
    if grid.bob_play_on_config["config"] == "L" or grid.bob_play_on_config["config"] == "L2":
        print("Is 1 L")
        return True
    return False

def solve_1_L(grid,bob_move):
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = grid.bob_play_on_config["j"]    
    dx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    # Bob 0,j-1 => Alice 2,j-1 same
    if (dx == -1 and ny == 0):
        rx,ry = get_real_pos(grid,-1,2,j,is_h_flip,is_v_flip)
        print("1 L a")
        return (rx,ry,color)
    # Bob 2,j-1 respc 1,j-1 => Alice 1,j-1 respc 2,j-1 available
    if(dx == -1 and ny == 2):
        cell = get_norm_cell(grid,-1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,-1,1,j,is_h_flip,is_v_flip)
        print("1 L b1")
        return (rx,ry,cell.color_options[0])
    if(dx == -1 and ny == 1):
        cell = get_norm_cell(grid,-1,2,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,-1,2,j,is_h_flip,is_v_flip)
        print("1 L b2")
        return (rx,ry,cell.color_options[0])
    
    # Bob 2,j => Alice 1,j-1 same if available else 3,j-1 same
    if (dx == 0 and ny == 2):
        cell = get_norm_cell(grid,-1,1,j,is_h_flip,is_v_flip)
        if color in cell.color_options :
            rx,ry = get_real_pos(grid,-1,1,j,is_h_flip,is_v_flip)
            print("1 L c1")
            return (rx,ry,color)
        else:
            rx,ry = get_real_pos(grid,-1,3,j,is_h_flip,is_v_flip)
            print("1 L c2")
            return (rx,ry,color)
        
    # Bob 3,j-1 x => Alice 1,j-1 x if possible else
    if (dx == -1 and ny == 3):
        cell_1_jm1 = get_norm_cell(grid,-1,1,j,is_h_flip,is_v_flip)
        cell_cpp = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
        if color in cell_1_jm1.color_options:
            rx,ry = get_real_pos(grid,-1,1,j,is_h_flip,is_v_flip)
            print("1 L d1")
            return (rx,ry,color)
        # if x != c'' => Alice 2,j x else Alice 0,j-1 c''
        else:
            
            if color != cell_cpp.value:
                rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
                print("1 L d2")
                return (rx,ry,color)
            else:
                rx ,ry = get_real_pos(grid,-1,0,j,is_h_flip,is_v_flip)
                print("1 L d3")
                return (rx,ry,cell_cpp.value)
    
    # Bob 3,j-2 or 1,j-2 => Alice 1,j-2
    if (dx == -2 and ny == 3) or (dx == -2 and ny == 1):
        cell = get_norm_cell(grid,-2,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,-2,1,j,is_h_flip,is_v_flip)
        print("1 L e")
        return (rx,ry,cell.color_options[0])

def is_1_Lp(grid,bob_move):
    x,y,color = bob_move
    if grid.bob_play_on_config["config"] == "L'" or grid.bob_play_on_config["config"] == "L'2":
        print("Is 1 L'")
        return True
    return False

def solve_1_Lp(grid,bob_move):
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = grid.bob_play_on_config["j"]
    dx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    # Bob 3,j+1 or 1,j+1 => Alice 2,j+1 c'' != c'
    if (dx == 1 and ny == 3) or (dx == 1 and ny == 1):
        cell_cp = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
        cell = get_norm_cell(grid,-1,0,j,is_h_flip,is_v_flip)

        #Check c'' != c' (0, j-1) is not c nether c' 
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("1 L' a")
        return (rx,ry,cell.color_options[0])

       
    # Bob 2,j+1 => Alice 1,j-1 aviable
    if (dx == 1 and ny == 2):
        cell = get_norm_cell(grid,-1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,-1,1,j,is_h_flip,is_v_flip)
        print("1 L' b")
        return (rx,ry,cell.color_options[0])
        
    #Bob 3,j-2 or 1,j-2 => Alice 1,j-1
    if (dx == -2 and ny == 3) or (dx == -1 and ny == 1):
        cell = get_norm_cell(grid,-1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,-1,1,j,is_h_flip,is_v_flip)
        print("1 L' c")
        return (rx,ry,cell.color_options[0])
    print("1 L' no condition matched")
    return

#Bob color doc of v not in gamma
def is_1_doc(grid,bob_move):
    x,y,color = bob_move
    if grid.bob_play_on_config["doctor"] == True:
        if grid.bob_play_on_config["config"] != "gm1":
            
            #check if its inside a block (not in the borders)
            print("1 doc: blocks:",grid.blocks)
            print("Is 1 doc")
            return True
    
    return False    

def solve_1_doc(grid,bob_move):
    
        patient = grid.bob_play_on_config["patient"]

        print("Solve 1 doc")
        return (patient.y,patient.x,patient.color_options[0])

#Bob color doc of v in gamma
def is_1_g_doc(grid,bob_move):
    x,y,color = bob_move
    if grid.bob_play_on_config["doctor"] == True:
        if grid.bob_play_on_config["config"] == 'gm1' and (grid.bob_play_on_config["j"] == x-1 or grid.bob_play_on_config["j"] == x+1):
            print("Is 1 g doc")
            return True
    return False

def solve_1_g_doc(grid,bob_move):
    x,y,color = bob_move
    other_doc = grid.bob_play_on_config["other_doc"]
    return (other_doc.y,other_doc.x,color)

#Bob color safe vertex
# A CHECK IL FAUT LA CONDITION DANS UN BLOCK
def is_1_safe(grid,bob_move):
    x,y,color = bob_move
    block = grid.blocks.block_at(x)
    if block is None or x == block.start_col or x == block.end_col:
        return False
    
    if grid.bob_play_on_config["state"] == "safe":
        print("Is 1 safe")
        return True

    return False

def solve_1_safe(grid,bob_move):

    '''Le TEmps de test les autres f'''

    # if E sick => Alice color it
    cell_sick = grid.get_first_sick_cell()
    if cell_sick is not None:
        print("1 safe a (sick)")
        return (cell_sick.y,cell_sick.x,cell_sick.color_options[0])
    
    # if E sound => Alice make it safe
    cell_sound = grid.get_first_sound_cell()
    if cell_sound is not None:
        print("1 safe b (sound)")
        return (cell_sound.y,cell_sound.x,cell_sound.color_options[0])
    
    # E uncolored safe not in border => Alice color it
    cell_safe = grid.get_first_inner_safe_cell()
    if cell_safe is not None:
        print("1 safe c (safe)")
        return (cell_safe.y,cell_safe.x,cell_safe.color_options[0])
    

    """
    In theory every vertex of a block is colored so alice try to play depending on the borders
    If there exist a border of x config we react
    """

    #1delta
    # config delta 1,j+2 != c' => A 1,j+1 c'
    # if 1,j+2 = c' => 0,j+1 c' 
    border_delta = grid.get_first_border_delta()
    #normalize border pos:
    if border_delta is not None:
        is_h_flip = border_delta["is_hori_flipped"]
        is_v_flip = border_delta["is_vert_flipped"]
        j = border_delta["j"]
        
        cell_1_jp2 = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
        cell_cp = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
        if cell_1_jp2.value != cell_cp.value :
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            print("1 safe delta a")
            return (rx,ry,cell_cp.value)
        else:
            rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
            print("1 safe delta b")
            return (rx,ry,cell_cp.value)

    
    #1 pi
    # A 3,j+1 c'
    border_pi = grid.get_first_pi()
    if border_pi is not None:
        is_h_flip = border_pi["is_hori_flipped"]
        is_v_flip = border_pi["is_vert_flipped"]
        j = border_pi["j"]

        cell_cp = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
        print("1 safe pi")
        return (rx,ry,cell_cp.value)

    #1 gamma
    # A 2,j aviable
    border_gamma = grid.get_first_gamma()
    if border_gamma is not None:
        is_h_flip = border_gamma["is_hori_flipped"]
        is_v_flip = border_gamma["is_vert_flipped"]
        j = border_gamma["j"]

        cell = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,0,2,j,is_h_flip,is_v_flip)
        print("1 safe gamma")
        return (rx,ry,cell.color_options[0])

    #1 alpha beta free 
    # if alpha => A 2,j+1 c
    # else if beta => A 2,j+1 c
    border_alpha = grid.get_first_alpha()
    border_beta = grid.get_first_beta()


    #1 beta
    # A 1,j+1 aviable
    if border_beta is not None:
        is_h_flip = border_beta["is_hori_flipped"]
        is_v_flip = border_beta["is_vert_flipped"]
        print("1 safe beta: border beta found at j=",border_beta["j"],"h_flip=",is_h_flip,"v_flip=",is_v_flip)
        j = border_beta["j"]

        cell = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("1 safe beta")
        return (rx,ry,cell.color_options[0])

    #1 alpha 1
    # if 1,j+2 != c => A 1,j+1 c
    if border_alpha is not None:
        is_h_flip = border_alpha["is_hori_flipped"]
        is_v_flip = border_alpha["is_vert_flipped"]
        j = border_alpha["j"]

        cell_c = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
        cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
        if cell_1_jp2.value != cell_c.value:
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            print("1 safe alpha a")
            return (rx,ry,cell_c.value)
        else:
    #1 alpha 2
    # else if j+3 empty => A 1,j+1 c'
            if is_column_empty(grid,3,j,is_v_flip):
                cell = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
                rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
                print("1 safe alpha b")
                return (rx,ry,cell.color_options[0])
    #1 aplha 3
    # else (j+3 not empty) => 1,j+1 c'
            else:
                cell = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
                rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
                print("1 safe alpha c")
                return (rx,ry,cell.color_options[0])
    return
"""
Case 2
-----##########-------
-------------##-------
-------------##-------
-------------##-------
-----##########-------
-----##---------------
-----##---------------
-----##---------------
-----##########-------
Bob play:
    - in border (not D, L or L')
"""

#Bob play in col of config delta
def is_2_delta(grid,bob_move):
    x,_,_ = bob_move
    if grid.bob_play_on_config["config"] == "d" and (x == grid.bob_play_on_config["j"]):
        print("Is 2 delta")
        return True
    return False

def solve_2_delta(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    #fix j
    j = x
    dx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)


    # if (2,j+2) != c' => Alice 1,j+1 c'
    cell_2_jp2 = get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip)
    cell_cp = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
    if cell_2_jp2.value != cell_cp.value :
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("2 Delta a")
        return (rx,ry,cell_cp.value)
    # else A 0,j+1 c'
    else:
        rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
        print("2 Delta b")
        return (rx,ry,cell_cp.value)

# Bob play in free border of a b or g
def is_2_abgF(grid,bob_move):
    x,_,_ = bob_move
    if grid.bob_play_on_config["config"] in ["a","b","g"] and (x == grid.bob_play_on_config["j"]):
        # check if it's free border
        j = grid.bob_play_on_config["j"]
        verti = grid.bob_play_on_config["is_vert_flipped"]
        if is_column_empty(grid,-1,j,verti) and is_column_empty(grid,-2,j,verti) :
            print("Is 2 abg free")
            return True
    return False

def solve_2_abgF(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    
    config = grid.bob_play_on_config["config"]
    j = x
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    # if B in alpha => Alice 2,j+1 c
    cell_c = get_norm_cell(grid,0,3,j,is_h_flip,is_v_flip)
    if config == "a":
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("2 abg free a")
        print("2 abg free a: c=",cell_c.value)
        return (rx,ry,cell_c.value)


    # if B in beta => Alice 2,j+1 c
    if config == "b":
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("2 abg free b")
        return (rx,ry,cell_c.value)

    # if B (2,j) c' != c (forcement different) in gamma => A (1,j+1) c'
    if config == "g" and ny == 2:
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("2 abg free g1")
        return (rx,ry,color)

    
    # if B (1,j) c' != c (forcement different) in gamma => A (2,j+1) c'
    if config == "g" and ny == 1:
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("2 abg free g2")
        return (rx,ry,color)
    

    return

def is_2_beta(grid,bob_move):
    x,_,_ = bob_move
    j= grid.bob_play_on_config["j"]
    if grid.bob_play_on_config["config"] == "b" and (x == j):
        print("Is 2 beta")
        return True
    return False

def solve_2_beta(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = grid.bob_play_on_config["j"]
    dx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #if Bob dont play 2,j => A 1,j+1 available
    cell_2_j = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
    if cell_2_j.value == 0:
        cell = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("2 beta a")
        return (rx,ry,cell_2_j.color_options[0])
    
    # if B 2,j c' => if 1,j+2 != c' => A 1,j+1 c'
    if cell_2_j.value != 0:
        cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
        if color != cell_1_jp2.value:
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            print("2 beta b1")
            return (rx,ry,color)
    # else if 0,j != c' => A 0,j+1 c'
        else:
            cell_0_j = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
            if color != cell_0_j.value:
                rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
                print("2 beta b2")
                return (rx,ry,color)
            #else gerer plus tard
    print("2 beta no condition matched")
    return

#Bob play in in non free Beta
def is_2_gamma(grid,bob_move):
    x,_,_ = bob_move
    j= grid.bob_play_on_config["j"]
    if grid.bob_play_on_config["config"] == "g" and (x == j):
        print("Is 2 gamma")
        return True

    return False

def solve_2_gamma(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = grid.bob_play_on_config["j"]
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #B 2,j => A 2,j+1 available
    if ny == 2 :
        cell = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("2 gamma a")
        return (rx,ry,cell.color_options[0])

    #B 1,j c' & 2,j+2 != c' => A 2,j+1 c'
    if ny == 1:
        cell_2_jp2 = get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip)
        if color != cell_2_jp2.value:
            rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
            print("2 gamma b")
            return (rx,ry,color)

    #else 2,j+1 c' => A 2,j) c'' (diff c et c')
        else:
            cell_c = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
            colors = [1,2,3,4]
            colors.remove(color)
            colors.remove(cell_c.value)
            rx,ry = get_real_pos(grid,0,2,j,is_h_flip,is_v_flip)
            print("2 gamma c")
            return (rx,ry,colors[0])

    return

# Bob play in non free alpha of at least size 2 
def is_2_alpha(grid,bob_move):
    x,_,_ = bob_move
    j= grid.bob_play_on_config["j"]
    verti = grid.bob_play_on_config["is_vert_flipped"]

    if is_column_empty(grid,-1,j,verti) and is_column_empty(grid,1,j,verti):
        return False
    
    if grid.bob_play_on_config["config"] == "a" and (x == j):
        print("Is 2 alpha")
        return True
    return False

def solve_2_alpha(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = grid.bob_play_on_config["j"]
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #if 2,j+2 != c => A 2,j+1 c
    cell_2_jp2 = get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip)
    cell_c = get_norm_cell(grid,2,0,j,is_h_flip,is_v_flip)
    if cell_2_jp2.value != cell_c.value:
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("2 alpha 1")
        return (rx,ry,cell_c.value)
    
    

    #Bob (0,j) c' & (2,j) not colored => A(1,j+1) c' if available else A(2,j+1) c'
    cell_2_j = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
    if ny == 0 and cell_2_j.value == 0:
        cell_1_jp1 = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
        if color in cell_1_jp1.color_options:
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            print("2 alpha 2.1")
            return (rx,ry,color)
        else:
            rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
            print("2 alpha 2.2")
            return (rx,ry,color)

    # B 0,j c' & 0,j not colored => if 1,j+2 != c' => A 1,j+1 c' else A 0,j+1 c'
    cell_0_j = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
    if ny == 0 and cell_0_j.value == 0:
        cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
        if color != cell_1_jp2.value:
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            print("2 alpha 3.1")
            return (rx,ry,color)
        else:
            rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
            print("2 alpha 3.2")
            return (rx,ry,color)

    # if (0,j+2) != c => A 0,j+1 c
    cell_0_jp2 = get_norm_cell(grid,2,0,j,is_h_flip,is_v_flip)
    if cell_0_jp2.value != cell_c.value:
        rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
        print("2 alpha 4")
        return (rx,ry,cell_c.value)

    # if (3,j+2) != c' => A 3,j+1 c'
    cell_3_jp2 = get_norm_cell(grid,2,3,j,is_h_flip,is_v_flip)
    cell_cp = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
    if cell_3_jp2.value != cell_cp.value:
        rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
        print("2 alpha 5")
        return (rx,ry,cell_cp.value)

    # (if 1,j+2) not c' should be the case Prop 3) => A 1,j+1 c' 
    cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
    if cell_1_jp2.value != cell_cp.value:
        print("By Prop 3 : 1,j+2 should not be c' ")
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("2 alpha 6")
        return (rx,ry,cell_cp.value)

    return

# Bob color v of non free 1 colom block alpha
def is_2_aplha_prime(grid,bob_move):
    x,_,_ = bob_move
    j= grid.bob_play_on_config["j"]
    verti = grid.bob_play_on_config["is_vert_flipped"]

    # not only 1 column in the block
    if not(is_column_empty(grid,-1,j,verti) and is_column_empty(grid,1,j,verti)):
        return False
    
    if grid.bob_play_on_config["config"] == "a" and (x == j):
        print("Is 2 alpha'")
        return True
    return False

# non free 2 col border
def solve_2_alpha_prime(grid,bob_move):

    
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = grid.bob_play_on_config["j"]
    
    
    cell_c = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)


    # if 2,j-2 != c => 2,j-1 c
    cell_2_jm2 = get_norm_cell(grid,-2,2,j,is_h_flip,is_v_flip)
    if cell_2_jm2.value != cell_c.value :
        rx,ry = get_real_pos(grid,-1,2,j,is_h_flip,is_v_flip)
        print("2 alpha' 0")
        return (rx,ry,cell_c.value)
    #(now asume that 2,j-2 is c)

    # if 0,j-2 != c => A 0,j-1
    cell_0_jm2 = get_norm_cell(grid,-2,0,j,is_h_flip,is_v_flip)
    if cell_0_jm2.value != cell_c.value and cell_0_jm2.value != 0:
        rx,ry = get_real_pos(grid,-1,0,j,is_h_flip,is_v_flip)
        print("2 alpha' 1a")
        return (rx,ry,cell_c.value)
    
    # else (=c) => if 1,j-2 colored => A 2mj-1 c'
    if cell_0_jm2.value == cell_c.value:
        cell_1_jm2 = get_norm_cell(grid,-2,1,j,is_h_flip,is_v_flip)
        if cell_1_jm2.value != 0:
            rx,ry = get_real_pos(grid,-1,2,j,is_h_flip,is_v_flip)
            print("2 alpha' 1b")
            return (rx,ry,cell_c.value)
    # ((0,j-2) colored & 1.j-2 = 0)
    # sup 0,j-2 = c and 1,j-2 = 0

    # if j-3 not empty => A 2,j-1 c'
    if not is_column_empty(grid,-3,j,is_v_flip):
        rx,ry = get_real_pos(grid,-1,2,j,is_h_flip,is_v_flip)
        print("2 alpha' 2")
        return (rx,ry,color)

    #if 2,j+2 != c => A 2,j+1 c
    cell_2_jp2 = get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip)
    if cell_2_jp2.value != cell_c.value:
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("2 alpha' 3")
        return (rx,ry,cell_c.value)
    
    # if (0,j+2) != c => A 0,j+1 c
    cell_0_jp2 = get_norm_cell(grid,2,0,j,is_h_flip,is_v_flip)
    if cell_0_jp2.value != cell_c.value and cell_0_jp2.value != 0:
        rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
        print("2 alpha' 4")
        return (rx,ry,cell_c.value)

    # if j+3 not empty => A 2,j+1 c'' != c'
    # if j+3 empty => A 2,j+1 c'' != c'
    
    #c''
    cpp = [1,2,3,4]
    cpp.remove(cell_c.value)
    cpp.remove(color)
    if not is_column_empty(grid,3,j,is_v_flip):
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("2 alpha' 5")
        return (rx,ry,cpp[0])
    else:
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("2 alpha' 6")
        return (rx,ry,cpp[0])


    return  


"""=-=-=--==-=-=--=-==-=--=-==--==-=-=--=-=-=-==--=---=-=-=-=
Case 3: Bob colors empty column

-----##########-------
-------------##-------
-------------##-------
-------------##-------
-----##########-------
-------------##-------
-------------##-------
-------------##-------
-----##########-------
Bob play:
    - empty col (not in j-1 of L,L2,L',L2')
"""

# Bob play in col j with j-1,j and j+1 empty 
def is_3_new(grid,bob_move):
    x,y,color = bob_move
    #previous and next column
    if x == 0 or x == grid.width-1:
        return False
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
    config = grid.bob_play_on_config["config"]
    config2 = grid.bob_play_on_config["config2"]
    if (config == "g" and (config2 == "a" or config2 == "b" or config2 == "g")):
        print("Is 3 gamma")
        return True
    
    return False
    
def solve_3_gamma(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = x+1 if is_v_flip else x-1
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)
    
    #3 gamma 1
    #B 3,j+1 x != c => A 2,j x
    cell_c = get_norm_cell(grid,0,0,j,is_h_flip,is_v_flip)
    if (ny == 3 and color != cell_c.value):
        rx,ry = get_real_pos(grid,0,2,j,is_h_flip,is_v_flip)
        print("3 gamma 1")
        return (rx,ry,color)

    #3 gamma 2
    #B 0,j+1 x != c => if 2,j+2 != c => A 2,j+1 x 
    if (ny == 0 and color != cell_c.value):
        cell_2_jp2 = get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip)
        if color != cell_2_jp2.value:
            rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
            print("3 gamma 2")
            return (rx,ry,color)
        
    #3 gamma 3
    #B 0,j+1 x != c => if 2,j+2 = c => A 2,j x
        else:
            rx,ry = get_real_pos(grid,0,2,j,is_h_flip,is_v_flip)
            print("3 gamma 3")
            return (rx,ry,color)
    
    print("3 gamma: no condition matched")
    return


def is_3_beta(grid,bob_move):

    config = grid.bob_play_on_config["config"]
    config2 = grid.bob_play_on_config["config2"]
    #print("Check 3 beta: ", config, config2)
    if (config == 'b' and (config2 == 'a' or config2 == 'b')):
        print("Is 3 beta")
        return True
    return False

def solve_3_beta(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = x+1 if is_v_flip else x-1
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #3 beta 0
    # B 2,j+1 respct 1,j+1 => A 1,j+1 respct A 2 j+1
    if (ny == 2):
        cell_1_jp1 = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("3 beta 0a")
        return (rx,ry,cell_1_jp1.color_options[0])
    if (ny == 1):
        cell_2_jp1 = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("3 beta 0b")
        return (rx,ry,cell_2_jp1.value)
    
    #3 beta 1
    #B 0,j+1 c => A 1,j+1 other
    cell_c = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
    if (ny == 0):
        cell_1_jp1 = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("3 beta 1")
        return (rx,ry,cell_1_jp1.color_options[0])

    #3 beta 2
    #B 3,j+1 c' != c => A 2,j 
    if (ny == 3):
        if color != cell_c.value:
            rx,ry = get_real_pos(grid,0,2,j,is_h_flip,is_v_flip)
            print("3 beta 2")
            return (rx,ry,color)

    #3 beta 3
    # if 0,j+2 != c => A 0,j+1 c
    cell_0_jp2 = get_norm_cell(grid,2,0,j,is_h_flip,is_v_flip)
    if cell_0_jp2.value != cell_c.value:
        rx,ry = get_real_pos(grid,1,0,j,is_h_flip,is_v_flip)
        print("3 beta 3")
        return (rx,ry,cell_c.value)
    
    # 3 beta 4
    # if 2,j+2 = c => A 1,j+1 any
    cell_2_jp2 = get_norm_cell(grid,2,2,j,is_h_flip,is_v_flip)
    if cell_2_jp2.value == cell_c.value:
        cell = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("3 beta 4")
        return (rx,ry,cell.color_options[0])

    # 3 beta 5
    # if 2,j+2 != c => A 1,j+1 x
    if cell_2_jp2.value != cell_c.value and cell_2_jp2.value != 0:
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("3 beta 5")
        return (rx,ry,color)
    
    # 3 beta 6
    # if 1,j+2 x => A 2,j+1 x
    cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)

    if cell_1_jp2.value != 0:
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("3 beta 6")
        return (rx,ry,cell_1_jp2.value)

    print("3 beta: no condition matched")
    return


def is_3_alpha(grid,bob_move):
    config = grid.bob_play_on_config["config"]
    config2 = grid.bob_play_on_config["config2"]
    if (config == "a" and (config2 == "a" )):
        print("Is 3 alpha")
        return True
    return False


# A CHECK LES CONFIG DEPENDE DES 2 COTES EN Un alpha peut etre flip et lautre non
def solve_3_alpha(grid,bob_move):
    #normalize bob move:
    x,y,color = bob_move
    is_h_flip = grid.bob_play_on_config["is_hori_flipped"]
    is_v_flip = grid.bob_play_on_config["is_vert_flipped"]
    j = x+1 if is_v_flip else x-1
    nx,ny = get_norm_pos(grid,x,y,j,is_h_flip,is_v_flip)

    #3 alpha 0
    # B 2,j+1 resp 1,j+1 => A 1,j+1 resp A 2 j+1
    if (ny == 2):
        cell_1_jp1 = get_norm_cell(grid,1,1,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("3 alpha 0a")
        return (rx,ry,cell_1_jp1.color_options[0])
    if (ny == 1):
        cell_2_jp1 = get_norm_cell(grid,1,2,j,is_h_flip,is_v_flip)
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("3 alpha 0b")
        return (rx,ry,cell_2_jp1.color_options[0])
    
    #3 alpha 1 (only case where 2 config alpha are sym vertical )
    # B 3,j+1 or 0,j+1 => A 1,j+1 c'
    #check if alpha aplha
    cell_1_jp2 = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
    cell_3_jp2 = get_norm_cell(grid,2,3,j,is_h_flip,is_v_flip)
    if (cell_1_jp2.value == cell_3_jp2.value and cell_1_jp2.value != 0):
        if (ny == 3 or ny == 0):
            rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
            print("3 alpha 1")
            return (rx,ry,cell_1_jp2.value)
        print("3 alpha 1: condition not met (should not happen if config is correct)")

    #3 alpha 2 ???
    # if c' != c => A 2,j+1 
    cell_c = get_norm_cell(grid,0,1,j,is_h_flip,is_v_flip)
    cell_cp = get_norm_cell(grid,2,1,j,is_h_flip,is_v_flip)
    if cell_cp.value != cell_c.value :
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("3 alpha 2")
        return (rx,ry,cell_cp.value)

    # 3 alpha 3
    # if B 3,j+1 x => 1,j+1 x
    if (ny == 3):
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("3 alpha 3")
        return (rx,ry,color)

    # 3 alpha 4
    # if 2,j != x -> A 2,j+1 x
    cell_2_j = get_norm_cell(grid,0,2,j,is_h_flip,is_v_flip)
    if cell_2_j.value != color :
        rx,ry = get_real_pos(grid,1,2,j,is_h_flip,is_v_flip)
        print("3 alpha 4")
        return (rx,ry,color)

    # 3 alpha 5
    # if col j+3 empty => A 1,j+1 x
    if is_column_empty(grid,3,j,is_v_flip):
        rx,ry = get_real_pos(grid,1,1,j,is_h_flip,is_v_flip)
        print("3 alpha 5")
        return (rx,ry,color)

    # 3 alpha 6
    # if if col j+3 not empty => 3,j+1 x
    else :
        rx,ry = get_real_pos(grid,1,3,j,is_h_flip,is_v_flip)
        print("3 alpha 6")
        return (rx,ry,color)

    print("3 alpha: no condition matched")
    return





#=========--------=========--------========--------=========--------======


""" 
input: list of (j,x) coordinates
return true if all the cells in the list have the same value
"""
def same_value_grid(grid,list):
    (j,y) = list[0]
    
    first_value = grid.get_cell(j,y).value
    for j,y in list: 
        if j < 0 or j >= grid.width or y < 0 or y >= grid.height:
            return False
        if grid.get_cell(j,y).value != first_value: 
            return False
    return True

"""ckeck if column j is empty from normized context """
def is_column_empty(grid,dx,j,verti):
    rj = j-dx if verti else j+dx

    if rj < 0 or rj >= grid.width:
        return True
    
    for y in range(grid.height):
        if grid.get_cell(rj,y).value != 0:
            return False
    return True


# for each fonction (a,j+b) => dx = b ; y=a ; j = j
"""
input: grid, dx, y, j, is_hori_flipped, is_vert_flipped
    dx is just the position relative to j
return: the cell at (x,y) on this context

"""
def get_norm_cell(grid,dx,y,j,hori,verti):

    if hori and verti:
        #print("strategy: dx,y,j , nx,ny ",dx,y,j,2*j-dx,grid.height-1-y)
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

def is_inside_block(grid,x,y):
    block = grid.blocks