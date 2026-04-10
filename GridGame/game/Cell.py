
class Cell:
    def __init__(self, x, y, grid,num_colors=4, value=0):
        self.grid = grid
        self.x = x
        self.y = y
        self.grid_width = grid.width
        self.grid_height = grid.height

        self.num_colors = num_colors

        #used to track rounds in advanced strategies
        self.round=None

        self.value = value #color value, 0 if uncolored

        self.any_color = False #used to show x on cell

        self.neighbors = []

        self.neighbors_color = self.get_neighbor_colors() 
        self.neighbors_to_color = self.number_of_neighbors() #number of neighbors yet to be colored
        self.color_options = [i for i in range(1,num_colors+1)] #remaining color options

        self.played_by = None #0 or 1 for Alice or Bob

        self.is_safe = False
        self.is_sound = False
        self.is_color_critical = False
        self.is_uncolorable = False

        self.doctors = []
        #doctors has only one patient
        self.patients = []

    #return the colors of the neighboring cells


    #check and update the status of the cell
    #also return the list of cells affected byt he update
    def update_cell(self):
        affected = []
        self.is_safe = False
        
        #check if its critical
        if len(self.color_options) == 1 and not self.is_safe:
            print(f"Cell at ({self.x}, {self.y}) is color critical")
            self.is_color_critical = True

        #is safe?
        affected += self.check_safe_cell()
        #is sound?
        affected += self.check_sound_cell()


        #check if sick


        #check if no color options left
        if len(self.color_options) == 0:
            self.is_uncolorable = True
            print(f"Cell at ({self.x}, {self.y}) has no color options left")
        
        #print(f"Cell: affected={len(affected)}")
        return affected

    def check_safe_cell(self):
        affected = []

        #check if its safe
        #is colorred OR #N <= 3 OR 2 neighbors colored with same color
        #OR 3 neighbors colored with 3 colors but the 4th is neighbor to the last color
        if self.value != 0:
            self.is_safe = True

        neighbor_colors = self.get_neighbor_colors()
        #print(f"CELL 1st test:{len(self.neighbors)<4 } 2nd: {len(neighbor_colors)> len(set(neighbor_colors))} ")
        
        if self.value != 0 or len(self.neighbors) < self.num_colors or len(neighbor_colors) - len(set(neighbor_colors)) > 0 :
            
            self.is_safe = True
            #print(f"Cell at ({self.x}, {self.y}) is safe")

        if len(self.neighbors) == 4 and len(set(self.neighbors_color)) == 3:
            #affected.append(self.clone_cell())
            missing_color = self.color_options[0] if len(self.color_options) > 1 else []
            print(f"Cell at ({self.x}, {self.y}) is check uncolored neighbor")
            uncolored_neighbor = self.get_uncolored_neighbor()
            if uncolored_neighbor is not None:
                if missing_color in uncolored_neighbor.neighbors_color:
                    self.is_safe = True
                    print(f"Cell at ({self.x}, {self.y}) is safe by neighbor colors")
        return affected
    
    #check if sound
    #return the list of affected cells
    def check_sound_cell(self):
        #check if cell is in block
        if self.grid.blocks:
            block = self.grid.blocks.block_at(self.y)
            if block == None:
                self.is_sound = False
                return []

        if self.is_safe:
            return []
        
        if len(self.doctors) == 2:
            return []
        #check if sound
        #sound if 2 neighbors are safe and become doctors.(doctors can only have 1 patient)

        affected = []
        #sound va me rendre fou 
        safe_doctor_neighbors = []
        for neighbor in self.neighbors:
            if neighbor.is_safe and (not neighbor.is_doctor()) and neighbor.value == 0:
                safe_doctor_neighbors.append(neighbor)

        if len(safe_doctor_neighbors) >= 2:
            #affected.append(safe_doctor_neighbors[0].clone_cell())
            #affected.append(safe_doctor_neighbors[1].clone_cell())

            safe_doctor_neighbors[0].patients.append(self)
            safe_doctor_neighbors[1].patients.append(self)
            self.doctors.append(safe_doctor_neighbors[0])
            self.doctors.append(safe_doctor_neighbors[1])
            self.is_sound = True
        if len(self.doctors) == 0:
            self.is_sound = False

        return affected

    #to simplify the detection of safe cells
    def number_of_neighbors(self):
        #at minimum border cells have 2 neighbors
        result = 2
        #not in the x borders
        if not (self.x == 0 or self.x ==  self.grid_width -1):
            result += 1

        #not in the y borders
        if not (self.y == 0 or self.y ==  self.grid_height -1):
            result += 1
        return result

    #change the value of the cell
    def set_value(self, value, player="A"):
        self.value = value
        self.played_by = player

    def get_value(self):
        return self.value

    def get_player(self):
        return self.played_by

    def is_doctor(self):
        return len(self.patients) > 0

    def get_uncolored_neighbor(self):
        for neighbor in self.neighbors:
            if neighbor.get_value() == 0:
                return neighbor
        return None
    #return the status safe/sound/color_critical/doctor/patient

    def get_status(self):
        if self.is_uncolorable:
            return "x"
        if self.is_safe:
            return "safe"
        if self.is_sound:
            return "sound"
        if self.is_color_critical:
            return "cc"
        
        return "o"
    
    def get_empty_neighbors(self):
        return [neighbor for neighbor in self.neighbors if neighbor.value == 0]

    def get_neighbor_colors(self):
        return [neighbor.value for neighbor in self.neighbors if neighbor.value != 0]
    
    '''
    def clone_cell(self):
        clone = []
        clone.neighbors_color = [] 
        return clone
    '''
    

    #debug/analysis print (with right click)
    def print_cell_informations(self):
        print("=--=--=--=--=--=--=--=--=--=--=--=--=--=--=")
        print(f"Cell ({self.x}, {self.y}):")
        print(f"  Value: {self.value}")
        print(f"  Played by: {self.played_by}")
        print(f"  Neighbors: {[(n.x, n.y) for n in self.neighbors]}")
        print(f"  Neighbors colors: {self.neighbors_color}")
        print(f"  Neighbors to color: {self.neighbors_to_color}")
        print(f"  Color options: {self.color_options}")
        print(f"  Is safe: {self.is_safe}")
        print(f"  Is sound: {self.is_sound}")
        print(f"  Is color critical: {self.is_color_critical}")
        print(f"  Is uncolorable: {self.is_uncolorable}")
        print(f"  Doctors: {[(d.x, d.y) for d in self.doctors]}")
        print(f"  Patients: {[(p.x, p.y) for p in self.patients]}")
        print("is_doctor: ", self.is_doctor())
        print("=--=--=--=--=--=--=--=--=--=--=--=--=--=--=")
        


    #test undo diff
    #retourne une sauvegarde de letat d'une cell
    def get_state(self):
        return {
            "value": self.value,
            "color_options": self.color_options[:], # Copie de la liste !
            "neighbors_to_color": self.neighbors_to_color,
            "is_safe": self.is_safe,
            "is_sound": self.is_sound,
            "is_color_critical": self.is_color_critical,
            "is_uncolorable": self.is_uncolorable,
            "played_by": self.played_by,
            "round": self.round,
            #on save les coo pour restaurer plus facilement
            "doctors_coords": [(d.x, d.y) for d in self.doctors],
            "patients_coords": [(p.x, p.y) for p in self.patients],

        }

    #restaure lancien etat des cells
    def restore_state(self, state, grid):
       
        self.value = state['value']
        self.color_options = state['color_options'][:]
        self.neighbors_to_color = state['neighbors_to_color']
        self.is_safe = state['is_safe']
        self.is_sound = state['is_sound']
        self.is_color_critical = state['is_color_critical']
        self.is_uncolorable = state['is_uncolorable']
        self.played_by = state['played_by']
        self.round = state['round']
        
        # Reconstruction des objets à partir des coordonnées
        # On va chercher les vrais objets dans la grille actuelle
        self.doctors = [grid.nodes[x][y] for x, y in state['doctors_coords']]
        self.patients = [grid.nodes[x][y] for x, y in state['patients_coords']]