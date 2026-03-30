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
    def move_played(self,x,y,color,player_name):
        
        #keep the config on which Bob played for Alice strategy
        print("block_height_4: Bob played on config: ", self.get_config_at(x))
        if player_name == "B":
            self.grid.bob_play_on_config = self.get_config_at(x)

        self.update_block(x)
        right_block_start = self.get_right_block(self.block_at(x))
        self.update_block(right_block_start) if right_block_start != None else None


        return

    def update_all_blocks(self):
        for block in self.blocks:
            block.check_configurations()

    #test for undo
    def rebuild_from_grid(self):
        """Rebuild all blocks/configurations from current grid state."""
        self.blocks = []

        for x in range(self.width):
            col_has_color = any(self.grid.get_cell(x, y).value != 0 for y in range(self.height))
            if col_has_color:
                self.update_block(x)

    def evaluate_block(self):

        return
    
    def update_block(self,x):
        block = self.block_at(x)
        if block == None:
            block_left = self.block_at(x-1)
            block_right = self.block_at(x+1)

            if(block_left):
                #Notes: si c'est bob on aimerais save la config du bord pour reagir en consequence
                #self.grid.bob_play_on_config["config"] = block_left.right_configuration
                #self.grid.bob_play_on_config["is_hori_flipped"] = block_left.is_right_flipped
                

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
        if block.right_configuration == 'p':
            self.block_at(x+2).left_configuration = 'p'
            self.block_at(x+2).is_left_flipped = block.is_right_flipped
            self.block_at(x+2).pi_side = block.pi_side
            print("block_height_4: change right block config to p")
        if block.left_configuration == 'p':
            #self.grid.bob_play_on_config["is_vert_flipped"] = True
            self.block_at(x-2).right_configuration = 'p'
            self.block_at(x-2).is_right_flipped = block.is_left_flipped
            self.block_at(x-2).pi_side = block.pi_side
        #block.print_block()
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
    
    """
    input: column x
    output: {"config": char ,"config2":char, "is_hori_flipped" : bool, "is_vert_flipped": bool, "j": int}
    """
    def get_config_at(self,x):
        block = self.block_at(x)
        if block:
            if block.particular_configs:
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
                    print("block_height_4: D2' x=", x, "config[1]=", config[1])
                    print("block_height_4: ",config[0]) 
                    if config[0] == "D2'" and (config[1]-1 == x-1 or config[1] == x or config[1]+1 == x or config[1]+2  == x ) and config[3] == False:
                        print("block_height_4: Bob played on config D2' C")
                        return {"config": "D2'", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":False,"j": config[1]}
                    
                    # D2' flipped verticalement
                    if config[0] == "D2'" and (config[1]-2 == x-2 or config[1] == x-1 or config[1] == x or config[1]+1 == x) and config[3] == True:
                        print("block_height_4: Bob played on config D2' D ")
                        return {"config": "D2'", "config2": None, "is_hori_flipped": config[2], "is_vert_flipped":True,"j": config[1]}
                    
                    
                    
            #SI ON JOUE DANS UNE BORDURE? 
            if x == block.start_col:
                if block.left_configuration:
                    print("block_height_4: Bob played on left border config")
                    return {"config": block.left_configuration, "config2": None, "is_hori_flipped": block.is_left_flipped, "is_vert_flipped": False, "j": block.start_col}
            if x == block.end_col:
                if block.right_configuration:
                    print("block_height_4: Bob played on right border config")
                    return {"config": block.right_configuration, "config2": None, "is_hori_flipped": block.is_right_flipped, "is_vert_flipped": False, "j": block.end_col}
                
            return {"config": "Not particular","config2": None, "is_hori_flipped": False, "is_vert_flipped": False}

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
                    print("block_height_4: 1")
                    return {"config": 'p',"config2": 'p', "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}
                else:
                    print("block_height_4: 2")
                    return {"config": 'p',"config2": 'p', "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": True, "j": block_left.start_col}
                
            if block_right.left_configuration == 'p':
                self.grid.bob_play_on_config["is_vert_flipped"] = True
                if block_right.pi_side == "left":
                    print("block_height_4: 3")
                    return {"config": 'p',"config2": 'p', "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": False, "j": block_right.start_col}
                else:
                    print("block_height_4: 4")
                    return {"config": 'p', "config2": 'p', "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": True}
            
            #if l or r is in None we keep the other config
            if block_left.right_configuration == None:
                print("block_height_4: 5")
                return {"config": block_right.left_configuration,"config2": None, "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": True, "j": block_right.start_col}
            if block_right.left_configuration == None:
                print("block_height_4: 6")
                return {"config": block_left.right_configuration,"config2": None, "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}
            
            # 2 blocks have config
            # need to sort (config and config2)
            print("block_height_4: 7")
            return {"config": block_left.right_configuration,"config2": block_right.left_configuration, "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}  


        #if bob play side to only 1 block
        #left
        if block_left and block_right == None:
            return {"config": block_left.right_configuration, "config2": "empty", "is_hori_flipped": block_left.is_right_flipped, "is_vert_flipped": False, "j": block_left.start_col}
        #right
        if block_right and block_left == None:
            return {"config": block_right.left_configuration, "config2": "empty", "is_hori_flipped": block_right.is_left_flipped, "is_vert_flipped": True, "j": block_right.start_col}
        
        #bob play on empty col with no block around
        return {"config": 'none', "config2": "empty", "is_hori_flipped": False, "is_vert_flipped": False, "j": None}