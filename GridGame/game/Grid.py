"""
This file contains the implementation of the Grid class, which represents the game grid in the GridGame.
The Grid class manages the state of the game, including the cells, their colors, and the interactions between players (Alice and Bob). It provides methods for validating moves, updating the grid state, and checking the status of cells (safe, sound, color critical, uncolorable).
"""
from game.Cell import Cell
#from game.Block import Block

#possible colors:
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    dictionary = {0:"WHITE", 1:"RED", 2:"GREEN", 3:"YELLOW", 4:"BLUE", 5:"MAGENTA", 6:"CYAN", 7:"WHITE"}

class Grid:
    #for now grid is defined as an matrix of cells with colors represented by integers
    def __init__(self, height, width, num_colors=4):
        self.width = width
        self.height = height
        self.nodes = [[Cell(x, y, self ,num_colors=num_colors) for y in range(width)] for x in range(height)]
                
        self.last_moves = [] # (x,y,color)
        self.previous_changes = [] #list of list on changes for each move
        self.num_colors = num_colors
        self.blocks = []
        self.player = 0 #0 for Alice, 1 for Bob
        self.round = 1
        
        
        self.last_Bob_move = None # (x,y,color,past_config) 

        # dic with the config and the flips to normelize 
        # "config2": can be:
        # None -> there is a block but no config
        # Empty -> there is no block
        # char -> block with config char     
        self.bob_play_on_config = {"config":'',"config2":"","is_hori_flipped":False,"is_vert_flipped":False}
        #might have to keep left and right on some cases

        #add neighbors to each cell
        self.init_state()

        self.history = []

    def init_state(self):
        for i in range(self.width):
            for j in range(self.height):
                self.nodes[j][i].neighbors = self.neighborhood(self.nodes[j][i])

                #add the starting status of each cell
                self.nodes[j][i].check_safe_cell()
        for i in range(self.width):
            for j in range(self.height):
                self.nodes[j][i].check_sound_cell()

    # check if the move respect the coloring property
    def is_move_valid(self, x, y, value):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            #print(f"Move out of bounds: ({x}, {y})")
            return False
        for neighbor in self.nodes[y][x].neighbors:
            if neighbor.value == value:
                #print(f"Invalide move {x},{y} val: {value} already in neighbor at ({neighbor.x},{neighbor.y})")
                return False

        if 0 <= x < self.width and 0 <= y < self.height:
            if value in self.nodes[y][x].color_options:
                if self.nodes[y][x].value == 0:
                    return True
        return False
    
    #check if the move will kill Alice
    def is_move_kill_alice(self, x, y, value):
        #check if the move will create a dead node
        for neighbor in self.nodes[y][x].neighbors:
            if neighbor.value == 0 and value in neighbor.color_options and len(neighbor.color_options) == 1:
                return True
        return False
    
            




    def get_col(self, col_index):
        if 0 <= col_index < self.width:
            return [self.nodes[row][col_index] for row in range(self.height)]
        else:
            raise IndexError("Column index out of bounds")

    #joue le coup color en x y et update la grille 
    def play_move(self, x, y, color):
        if not self.is_move_valid(x, y, color):
            print(f"Invalid move at ({x}, {y})")
            return False
        

        #save pour undo
        self.last_Bob_move = (x,y,color)
        self.save_zone_snapshot(x, y, distance=2)

        #test config where bob play:
        



        #applique le coup
        target = self.nodes[y][x]
        target.value = color
        target.played_by = self.player
        target.round = self.round
        #manage if its a doctor / patient
        if target.is_doctor():
            patient = target.patients[0] 
            for doc in patient.doctors:
                doc.patients = []
            patient.doctors = []
        
        if target.doctors != []:
            for doc in target.doctors:
                doc.patients = []
            target.doctors = []

        
        
        target.update_cell()

        
        self.last_moves.append((x,y,color))
        self.update_neighbors(x,y,color)

        self.recompute_local_status(x, y, distance=2)

        return True

    def update_neighbors(self,x,y,color):
        cell = self.nodes[y][x]
        for neighbor in cell.neighbors:
            if color in neighbor.color_options:
                #self.add_to_previous_changes([neighbor.clone_cell()])

                neighbor.color_options.remove(color)
            neighbor.neighbors_to_color -= 1
            affected_cells = neighbor.update_cell()
            self.add_to_previous_changes(affected_cells)
        return 
    
            
    #utiliser dans la premier version de undo
    def roll_back_neighbors(self,x,y,color):
        cell = self.nodes[y][x]
        for neighbor in cell.neighbors:
            
            #check if we can restore the color option
            color_is_posible = True 
            for neighbor2 in neighbor.neighbors:
                #print(f"voisin2 value: {neighbor2.value}, color: {color}")
                if neighbor2.value == color:
                    color_is_posible = False
                    break
            if color_is_posible:
                neighbor.color_options.append(color)
            neighbor.neighbors_to_color += 1


    
            neighbor.update_cell()
            
            
    def get_cell(self, x, y): 
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.nodes[y][x]
        else:
            raise IndexError(f"Cell position out of bounds ({x},{y})")
            
    
    def empty_cells(self):
        empty = []
        for i in range(self.width):
            for j in range(self.height):
                if self.nodes[j][i].value == 0:
                    empty.append((i,j))
        return empty

    """
    #undo need to blank the last move, and restore the color options of the neighbors
    def undo_move(self):
        print("Undo:",self.last_moves[-1])
        if self.last_moves != []:
            x,y,color = self.last_moves.pop()
            self.nodes[y][x].value=0
            self.nodes[y][x].played_by = ""
            self.nodes[y][x].round = None
            #restore the color options of the neighbors
            self.roll_back_neighbors(x,y,color)
            return True
        return False
    """
    #undo version avec zone de sauvegarde
    def undo_move(self):
        if not self.history:
            print("Rien à annuler")
            return False

        #recup de la save
        patch = self.history.pop()

        #restoration 
        for (x, y), state in patch.items():
            self.nodes[y][x].restore_state(state, self)
        
        if self.last_moves:
            self.last_moves.pop()
        
        return True

    #add changed nodes to the last list of previous changes
    def add_to_previous_changes(self,changed_nodes):
        for node in changed_nodes:
            if self.previous_changes == [] or not(self.is_present(node,self.previous_changes[-1])):
                self.previous_changes[-1].append(node)


    #return true if node is in list 
    def is_present(self,node,list):
        for n in list:
            if n.x == node.x and n.y == node.y:
                return True
        return False
    

    def neighborhood(self,cell):
        i = cell.y
        j = cell.x
        neighborhood = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  
        for dx, dy in directions:
            nx, ny = i + dx, j + dy
            #check if we hit a border
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighborhood.append(self.nodes[ny][nx])
        return neighborhood
    

    def recompute_local_status(self, center_x, center_y, distance=2):
        min_x = max(0, center_x - distance)
        max_x = min(self.width, center_x + distance + 1)
        min_y = max(0, center_y - distance)
        max_y = min(self.height, center_y + distance + 1)

        # Passe 1: safe
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                self.nodes[y][x].check_safe_cell()

        # Passe 2: sound (dépend souvent de safe)
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                self.nodes[y][x].check_sound_cell()


    # get the first sick cell in the grid
    def get_first_sick_cell(self):
        for y in range(self.height):
            for x in range(self.width):
                if len(self.nodes[y][x].color_options) == 1 and self.nodes[y][x].value == 0:
                    return self.nodes[y][x]
                    
        return None

    def get_first_sound_cell(self):
        
        for y in range(self.height):
            for x in range(self.width):
                if self.nodes[y][x].is_sound and not self.nodes[y][x].is_safe:
                    #if inside a block
                    if self.blocks.block_at(y) is not None:
                        return self.nodes[y][x]
                    
        return None
    
    #get the first safe cell not in border
    def get_first_inner_safe_cell(self):
        # le mieux c'est surement de parcourir l'interieur des blocks
        for block in self.blocks.blocks:
            #col w/o border
            for col in block.columns[1:-1]:
                for cell in col:
                    if cell.is_safe and cell.value == 0:
                        return cell
            if block.end_col == self.width-1:
                for cell in block.columns[-1]:
                    if cell.is_safe and cell.value == 0:
                        return cell
        return None


    # return the number of color critical cells
    def get_number_of_cc_cells(self):
        count = 0
        for row in self.nodes:
            for cell in row:
                if cell.check_color_critical():
                     count += 1
        return count


    # return the number of dangerous color critical cells
    def get_number_of_dangerous_cc_cells(self):
        count = 0
        for row in self.nodes:
            for cell in row:
                if cell.check_dangerous_color_critical():
                     count += 1
        return count


    '''
    Function used in Case 1 safe
    return the first border in config X and the flips to normelize it
    '''
    # get the first border delta
    def get_first_border_delta(self):
        for block in self.blocks.blocks:
        
            if block.right_configuration == 'd':
                return {"config": block.right_configuration, "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}
            if block.left_configuration == 'd':
                return {"config": block.left_configuration, "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": True, "j": block.start_col}
        return None
    
    # get the first pi
    def get_first_pi(self):
        for block in self.blocks.blocks:
            if block.left_configuration == 'pi':
                return {"config": block.left_configuration, "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": True, "j": block.start_col}
            if block.right_configuration == 'pi':
                return {"config": block.right_configuration, "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}
        return None
    
    #get the first gamma
    def get_first_gamma(self):
        for block in self.blocks.blocks:
            if block.left_configuration == 'g':
                return {"config": block.left_configuration, "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": True, "j": block.start_col}
            if block.right_configuration == 'g':
                return {"config": block.right_configuration, "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}
        return None
    
    #get the first alpha/beta free
    def get_first_alpha_beta_free(self):
        for block in self.blocks.blocks:
            if block.left_configuration in ['a','b'] :
                return {"config": block.left_configuration, "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": True, "j": block.start_col}
            if block.right_configuration in ['a','b']:
                return {"config": block.right_configuration, "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}
        return None
    
    def get_first_alpha(self):
        for block in self.blocks.blocks:
            if block.left_configuration == 'a' :
                return {"config": block.left_configuration, "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": True, "j": block.start_col}
            if block.right_configuration == 'a' and block.end_col != self.width-1:
                return {"config": block.right_configuration, "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}
        return None
    
    def get_first_beta(self):
        for block in self.blocks.blocks:
            if block.left_configuration == 'b' :
                return {"config": block.left_configuration, "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": True, "j": block.start_col}
            if block.right_configuration == 'b' and block.end_col != self.width-1:
                return {"config": block.right_configuration, "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}
        return None

    def proportion_colored_cells(self):
        colored_cells = 0
        total_cells = self.width * self.height
        
        for row in self.nodes:
            for cell in row:
                if cell.value != 0:
                    colored_cells += 1
        
        return colored_cells / total_cells if total_cells > 0 else 0

    #test d'une autre logique de save, on garde une zone autour du coup jouer 
    # on grade les co des elements voisin pour les restorer apres sans garder les objets 
    def save_zone_snapshot(self, center_x, center_y, distance=2):
        
        patch = {}
        
        # Calcul des bornes pour ne pas sortir de la grille
        min_x = max(0, center_x - distance)
        max_x = min(self.width, center_x + distance + 1)
        min_y = max(0, center_y - distance)
        max_y = min(self.height, center_y + distance + 1)

        # On boucle sur la zone carrée
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                # On sauvegarde l'état AVANT modif
                patch[(x, y)] = self.nodes[y][x].get_state()
        
        self.history.append(patch)
