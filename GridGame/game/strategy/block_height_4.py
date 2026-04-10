from turtle import left

from game.strategy.Block4 import Block

class BlockHeight4:
    def __init__(self,grid):

        self.blocks = []
        self.grid = grid
        self.height = grid.height
        self.width = grid.width


    """
    input: move played by Bob (x,y,color)
    output: void
    result: update the configuration of the block
    """
    def move_played(self,x,y,color,player_name,is_doc, status_before_move,patient = None,other_doc = None):
        
        #keep the config on which Bob played for Alice strategy
        #print("block_height_4: Bob played on config: ", self.get_config_at(x))
        if player_name == "B":
            self.grid.bob_play_on_config = self.get_config_at(x)
            cell = self.grid.get_cell(x,y)
            if is_doc:
                self.grid.bob_play_on_config["doctor"] = True
                self.grid.bob_play_on_config["patient"] = patient
                self.grid.bob_play_on_config["other_doc"] = other_doc
            else:
                self.grid.bob_play_on_config["doctor"] = False
            if cell.is_safe:
                self.grid.bob_play_on_config["state"] = status_before_move

        self.update_block(x)
        #print("block_height_4: update block at x=", x)  
        
        
        left_block_end = self.get_left_block(self.block_at(x))
        if left_block_end != None:
            #print("block_height_4: left block end=", left_block_end)    
            self.update_block(left_block_end) if left_block_end != None else None
            

        right_block_start = self.get_right_block(self.block_at(x))
        if right_block_start != None:
            #print("block_height_4: right block start=", right_block_start)
            self.update_block(right_block_start)
            

        self.update_pi(self.block_at(x))
        if left_block_end != None:
            self.update_pi(self.block_at(left_block_end))
            #self.block_at(left_block_end).print_info() 
        if right_block_start != None:
            self.update_pi(self.block_at(right_block_start))
            #self.block_at(right_block_start).print_info()
        #self.block_at(x).print_info()   


        return

        
    def update_pi(self,block):
        
        if block.right_configuration == 'p':
            x = block.end_col
            #print("block_height_4: block at x+2", self.block_at(x+2))
            #print("block_height_4: block at x+2=", x+2)
            self.block_at(x+2).left_configuration = 'p'
            self.block_at(x+2).is_left_flipped = block.is_right_flipped
            self.block_at(x+2).pi_side = block.pi_side
            #print("block_height_4: change right block config to p")
        if block.left_configuration == 'p':
            x = block.start_col
            #self.grid.bob_play_on_config["is_vert_flipped"] = True
            self.block_at(x-2).right_configuration = 'p'
            self.block_at(x-2).is_right_flipped = block.is_left_flipped
            self.block_at(x-2).pi_side = block.pi_side
            #print("block_height_4: change left block config to p")



    def update_all_blocks(self):
        for block in self.blocks:
            block.check_configurations()

    
    """Rebuild contiguous non-empty blocks from grid state, without computing configurations."""
    def rebuild_blocks_only(self):
        self.blocks = []
        x = 0

        while x < self.width:
            # Skip empty columns
            while x < self.width and all(self.grid.get_cell(x, y).value == 0 for y in range(self.height)):
                x += 1

            if x >= self.width:
                break

            # Start of a new contiguous block
            start = x
            columns = []

            while x < self.width and any(self.grid.get_cell(x, y).value != 0 for y in range(self.height)):
                columns.append([self.get_cell(x, row) for row in range(self.height)])
                x += 1

            block = Block(self)
            block.start_col = start
            block.end_col = x - 1
            block.size = block.end_col - block.start_col + 1
            block.columns = columns
            self.blocks.append(block)


    #test for undo
    def rebuild_from_grid(self):
        """Rebuild all blocks/configurations from current grid state."""
        self.rebuild_blocks_only()
        self.update_all_blocks()

    def evaluate_block(self):

        return
    
    def update_block(self,x):
        block = self.block_at(x)
        if block == None:
            block_left = self.block_at(x-1)
            block_right = self.block_at(x+1)

            if(block_left):

                block_left.end_col = x
                block_left.size += 1
                block_left.columns.append([self.get_cell(x, row) for row in range(self.height)])
                #merge 2 blocks

                if(block_right):
                    block_left.end_col = block_right.end_col
                    block_left.size += block_right.size
                    block_left.columns.extend(block_right.columns)
                    self.blocks.remove(block_right)
                    
                block_left.check_configurations()
                #block_left.print_block()
                return
                      
            if(block_right):
                #idem que block_left pour les configs
                #self.grid.bob_play_on_config["config"] = block_right.left_configuration
                #self.grid.bob_play_on_config["is_hori_flipped"] = block_right.is_left_flipped
                #self.grid.bob_play_on_config["is_vert_flipped"] = True
                #print("block_height_4: Bob play on config: ", self.grid.bob_play_on_config)

                block_right.start_col = x
                block_right.size += 1
                block_right.columns.insert(0,[self.get_cell(x, row) for row in range(self.height)])
                block_right.check_configurations()
                #block_right.print_block()
                
                return
            
            #create new block
            block = Block(self)
            block.start_col = x
            block.end_col = x
            block.size = 1
            block.columns.append([self.get_cell(x, row) for row in range(self.height)])
            self.blocks.append(block)


        block.check_configurations()
        
        return


    def block_at(self, x):
        for block in self.blocks:
            if block.start_col <= x <= block.end_col:
                return block
        return None
    
    def get_cell(self, x, y):
        return self.grid.get_cell(x, y)
    

    #to update the configuration of the block pour pi,L,D... whene we play on the left block
    #return the line of the right block
    def get_right_block(self, block):
        for b in self.blocks:
            if b.start_col > block.end_col:
                return b.start_col
        return None
    
    def get_left_block(self, block):
        for b in reversed(self.blocks):
            if b.end_col < block.start_col:
                return b.end_col
        return None
    
    """
    input: column x
    output: {"config": char ,"config2":char, "is_hori_flipped" : bool, "is_vert_flipped": bool, "j": int}
    """
    def get_config_at(self,x):
        block = self.block_at(x)
        if block:
            if block.particular_configs:
                print("block_height_4: block at x=", x, " has particular configs: ", block.particular_configs)
                for config in block.particular_configs:
                    if config[0] == "D" and (config[1]+1 == x or config[1]+2 == x):
                        print("block_height_4: Bob played on config D")
                        return {"config": "D", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":False,"j": config[1]}
                    
                    # D' 
                    if config[0] == "D'" and (config[1]-1 == x or config[1] == x or config[1]+1 == x or config[1]+2 == x) and config[3] == False:
                        print("block_height_4: Bob played on config D' A")
                        return {"config": "D'", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":False,"j": config[1]}
                    #D' flipped verticalement
                    if config[0] == "D'" and (config[1]-2 == x or config[1] == x-1 or config[1] == x or config[1]+1 == x) and config[3] == True:
                        print("block_height_4: Bob played on config D' B")
                        return {"config": "D'", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":True,"j": config[1]}

                    # D2'
                    #print("block_height_4: D2' x=", x, "config[1]=", config[1])
                    #print("block_height_4: ",config[0]) 
                    if config[0] == "D2'" and (config[1]-1 == x-1 or config[1] == x or config[1]+1 == x or config[1]+2  == x ) and config[3] == False:
                        print("block_height_4: Bob played on config D2' C")
                        return {"config": "D2'", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":False,"j": config[1]}
                    
                    # D2' flipped verticalement
                    if config[0] == "D2'" and (config[1]-2 == x-2 or config[1] == x-1 or config[1] == x or config[1]+1 == x) and config[3] == True:
                        print("block_height_4: Bob played on config D2' D ")
                        return {"config": "D2'", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":True,"j": config[1]}
                    
                    
                    
            #SI ON JOUE DANS UNE BORDURE? 
            if x == block.start_col: 
                #test !=0 pour eviter la col tt a guache soit jouer comme bordure
                if block.left_configuration and x != 0:
                    print("block_height_4: Bob played on left border config")
                    return {"config": block.left_configuration, "config2": None, "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": True, "j": block.start_col}
            if x == block.end_col:
                if block.right_configuration and x != self.width-1:
                    print("block_height_4: Bob played on right border config")
                    return {"config": block.right_configuration, "config2": None, "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}
                
            if x-1 == block.start_col and block.left_configuration == 'g':
                return {"config": "gm1","config2": "gm1", "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": True, "j": block.start_col}
            
            if x+1 == block.end_col and block.right_configuration == 'g':
                return {"config": "gm1","config2": "gm1", "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}

            return {"config": "Not particular","config2": None, "is_hori_flipped": False, "is_vert_flipped": False, "j": x}

        #Bob play on empty col

        block_left = self.block_at(x-1)
        block_right = self.block_at(x+1)
        # between 2 blocks
        if block_left and block_right:
            #in config L
            for config in block_right.particular_configs:
                # L
                if config[0] == "L" and (config[1]-2 == x or config[1]-1 == x or config[1] == x):
                    print("block_height_4: Bob played on config L")
                    return {"config": "L", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":False,"j": config[1]} 
                # L2
                if config[0] == "L2" and (config[1]-2 == x or config[1]-1 == x or config[1] == x):
                    print("block_height_4: Bob played on config L2")
                    return {"config": "L2", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":False,"j": config[1]}
                # L'
                if config[0] == "L'" and (config[1] - 2 == x or config[1] - 1 == x or config[1] == x or config[1]+1 == x) :
                    print("block_height_4: Bob played on config L'")
                    return {"config": "L'", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":False,"j": config[1]} 
                # L2'
                if config[0] == "L2'" and (config[1] - 2 == x or config[1] - 1 == x or config[1] == x or config[1]+1 == x) :
                    print("block_height_4: Bob played on config L2'")
                    return {"config": "L2'", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":False,"j": config[1]}

            # in config pi
            if block_left.right_configuration == 'p':
                if block_left.pi_side == "left":
                    return {"config": 'p',"config2": 'p', "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}
                else:
                    return {"config": 'p',"config2": 'p', "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": True, "j": block_left.start_col}
                
            if block_right.left_configuration == 'p':
                self.grid.bob_play_on_config["is_vert_flipped"] = True
                if block_right.pi_side == "left":
                    return {"config": 'p',"config2": 'p', "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": False, "j": block_right.start_col}
                else:
                    return {"config": 'p', "config2": 'p', "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": True}
            
            #if l or r is in None we keep the other config
            if block_left.right_configuration == None:
                return {"config": block_right.left_configuration,"config2": None, "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": True, "j": block_right.start_col}
            if block_right.left_configuration == None:
                return {"config": block_left.right_configuration,"config2": None, "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}
            
            # 2 blocks have config
            # need to sort (config and config2)
            # gamma > beta > alpha
            left_config = block_left.right_configuration
            right_config = block_right.left_configuration

            if left_config == 'g' :
                return {"config": left_config,"config2": right_config, "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}
            if right_config == 'g' :
                return {"config": right_config,"config2": left_config, "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": True, "j": block_right.start_col}
            
            if left_config == 'b':
                return {"config": left_config,"config2": right_config, "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}
            if right_config == 'b':
                return {"config": right_config,"config2": left_config, "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": True, "j": block_right.start_col}
            
            # should be only alpha alpha left
            return {"config": block_left.right_configuration,"config2": block_right.left_configuration, "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}  


        #if bob play side to only 1 block
        #left
        if block_left and block_right == None:
            #EXCEPTION IF j=0 then consider as beta
            if x-1 == 0:
                return {"config": 'b', "config2": "empty", "is_hori_flipped": False, "is_vert_flipped": False, "j": 0}
            
            return {"config": block_left.right_configuration, "config2": "empty", "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.end_col}
        #right
        if block_right and block_left == None:
            return {"config": block_right.left_configuration, "config2": "empty", "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": True, "j": block_right.start_col}
        
        #bob play on empty col with no block around
        return {"config": 'none', "config2": "empty", "is_hori_flipped": False, "is_vert_flipped": False, "j": x}
    
    #check the 5 induction hypothesis to check if they hold after Alice move
    def check_induction_hypothesis(self):
        print("IH check: start")

        #1. Every vertex of a block is safe sound or sick (no none or cc)
        print("IH 1. check:",end=' ')
        for block in self.blocks:
            for col in block.columns:
                for cell in col:
                    if not (cell.is_safe or cell.is_sound):#or cell.is_sick
                        print("1. check failed: block at x=", block.start_col, " has a vertex with value ", cell.value)
                        print("1. Every vertex of a block is safe or sound or sick.")
                        return False
        print("1. passed")

        #2. every border of block is alpha/beta/gamma/delta/pi
        print("IH 2. check:",end=' ')
        for block in self.blocks:
            if block.left_configuration and block.left_configuration not in ['a','b','g','d','p']:
                print(" 2. check failed: block at x=", block.start_col, " has left border config ", block.left_configuration)
                print("2. Every border of a block is in configuration α, β, γ, δ or π.")
                return False
            if block.right_configuration and block.right_configuration not in ['a','b','g','d','p']:
                print(" 2. check failed: block at x=", block.start_col, " has right border config ", block.right_configuration)
                print("2. Every border of a block is in configuration α, β, γ, δ or π.")
                return False
        print("2. passed")

        #3. no border have 4 verticices colored with only 2 colors
        print("IH 3. check:",end=' ')
        for block in self.blocks:
            a,b,c,d = block.columns[0]
            if a == c and b == d and a != 0 and b != 0:
                print(" 3. check failed: block at x=", block.start_col, " has left border with 4 vertices colored with only 2 colors")
                print("3. No border has its 4 vertices colored with only two colors.")
                return False
            
            e,f,g,h = block.columns[-1]
            if e == g and f == h and e != 0 and f != 0:
                print(" 3. check failed: block at x=", block.end_col, " has right border with 4 vertices colored with only 2 colors")
                print("3. No border has its 4 vertices colored with only two colors.")
                return False
        print("3. passed")
        #4. no vertex of border alpha is doctor
        print("IH 4. check:",end=' ')
        for block in self.blocks:
            if block.left_configuration == 'a':
                for col in block.columns:
                    for cell in col:
                        if cell.is_doctor() and cell.y != 0:
                            print("4. check failed: block at x=", block.start_col, "y=",cell.x, "has left border with a vertex that is doctor")
                            print("4. No vertex of a border in configuration α is a doctor.")
                            return False
            if block.right_configuration == 'a':
                for col in block.columns:
                    for cell in col:
                        if cell.is_doctor():
                            print(" 4. check failed: block at x=", block.end_col, " has right border with a vertex that is doctor")
                            print("4. No vertex of a border in configuration α is a doctor.")
                            return False
        print("4. passed")
        #5. left border alpha has 2 uncolored vertices exepct j of Lambda/Lambda2/Lambda'/Lambda2' 
        print("IH 5. check:",end=' ')