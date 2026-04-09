#a block is a union of neighboring columns where each column has at least one colored cell
class Block:
    def __init__(self,grid):
        
        self.grid = grid
        self.columns = [] #list of columns in the block
        self.start_col = None
        self.end_col = None

        self.size = 0 #number of columns in the block

        self.is_safe = False
        self.is_sound = False
        self.is_sick = False

        self.configurations= ["a","b","g","d","p"] #alpha beta gamma delta pi
        self.right_configuration = None
        self.left_configuration = None

        self.flip_config_right = None #store the block fliped to match configurations (can be same as self)
        self.flip_config_left = None #store the block for the left config but flip it at right

        self.particular_configs = [] #list of particular config in the block 

        self.particular_config = None #dict to store node:config
        self.particular_config_j = None # index of the j for the particular config 
        self.particular_config_block = None #give the block with the particular config rotated

        self.particular_configs = []

        self.is_right_flipped = False
        self.is_left_flipped = False
        
        self.pi_side = None #side of the line full on pi config

    """
    functions to check the type of block:
    Illustration of the columns:
    ap a 0
    bp b 0
    cp c 0
    dp d 0
    (ap = a' ...)

    Structure:
    function is_xxx() -> get the values to check the config in 4 directions
    function xxx_config() -> get the normelized config to check if it match the config

    """
    #check if the block is of type alpha
    # b=c != 0, a and c not doctors and if colored then a != c
    def is_alpha(self):
        a,b,c,d = self.columns[0]
        first = self.alpha_config(a,b,c,d)
        revers = self.alpha_config(d,c,b,a)

        
        if revers:
            self.flip_config_left = self.flip_horizontal()
            self.is_left_flipped = True
            self.left_configuration = "a"
            
        if first:
            #block of 1 is always left alpha
            self.flip_config_left = self
            self.left_configuration = "a"

        #right side
        a,b,c,d = self.columns[len(self.columns)-1]
        first = self.alpha_config(a,b,c,d)
        revers = self.alpha_config(d,c,b,a)
        if revers:
            self.flip_config_right = self.flip_horizontal()
            self.is_right_flipped = True
            self.right_configuration = "a"

        if first:
            self.flip_config_right = self
            self.right_configuration = "a"

        
        
    def alpha_config(self,a,b,c,d):
        # b=c != 0
        if( (b.value == d.value and b.value !=0)):
            #a and c not doctors
            
            # On test sans les docs 
            if(a.value != c.value or a.value == 0 or c.value == 0):
                return True
            
            """Avec les docs:
            if((not(a.is_doctor()) and not(c.is_doctor()))):
                #print("Block4: alpha config b=d=",b.value)
                #if a and c colored then a != c
                if(a.value != c.value or a.value == 0 or c.value == 0):
                    return True
            """

    #check if the block is of type beta
    # b = cp and c=0 
    def is_beta(self):
        if self.size <2:
            return False
        
        #right side
        a,b,c,d = self.columns[len(self.columns)-1]
        ap, bp, cp, dp = self.columns[len(self.columns)-2]
        first = self.beta_config(b,c,cp)
        revers = self.beta_config(c,b,bp)
        
        #create fliped right
        if revers:
            self.flip_config_right = self.flip_horizontal()
            self.is_right_flipped = True
            self.right_configuration = "b"

        if first:
            self.flip_config_right = self
            self.right_configuration = "b"
        

        #left side
        a,b,c,d = self.columns[0]
        ap, bp, cp, dp = self.columns[1]
        first = self.beta_config(b,c,cp)
        revers = self.beta_config(c,b,bp)


        #create fliped horison vertic left
        if revers:
            self.flip_config_left = self.flip_vertical()
            fliped = self.flip_config_left
            self.flip_config_left = fliped.flip_horizontal()
            self.is_left_flipped = True
            self.left_configuration = "b"

        #create vertic fliped  
        if first:
            self.flip_config_left = self.flip_vertical()
            self.left_configuration = "b"


    def beta_config(self,b,c,cp):
        # b = cp and c=0
        if((b.value == cp.value and b.value !=0) and c.value == 0):
            return True

    #check if the block is of type gamma
    # a=d=bp != 0, b=c=cp = 0 and cp safe
    def is_gamma(self):
        if self.size <2:
            return False

        #right side
        a,b,c,d = self.columns[len(self.columns)-1]
        ap, bp, cp, dp = self.columns[len(self.columns)-2]
        first = self.gamma_config(a,b,c,d,ap,bp,cp,dp)
        revers = self.gamma_config(d,c,b,a,dp,cp,bp,ap)

        if revers:
            self.flip_config_right = self.flip_horizontal()
            self.is_right_flipped = True
            self.right_configuration = "g"


        if first:
            self.flip_config_right = self
            self.right_configuration = "g"
        
        #left side
        a,b,c,d = self.columns[0]
        ap, bp, cp, dp = self.columns[1]
        first = self.gamma_config(a,b,c,d,ap,bp,cp,dp)
        revers = self.gamma_config(d,c,b,a,dp,cp,bp,ap)

        
        if revers:
            self.flip_config_left = self.flip_vertical()
            fliped = self.flip_config_left
            self.flip_config_left = fliped.flip_horizontal()
            self.is_left_flipped = True
            self.left_configuration = "g"

        if first:
            self.flip_config_left = self.flip_vertical()
            self.left_configuration = "g"

        
    def gamma_config(self,a,b,c,d,ap,bp,cp,dp):
        # a=d=bp != 0
        if((a.value == d.value and a.value == bp.value and a.value !=0)):
            # b=c=cp = 0
            if(b.value ==0 and c.value ==0 and cp.value ==0):
                #cp safe
                if(cp.is_safe):
                    return True
    
    #check if the block is of type delta
    # a=bp !=0 , c != a != 0
    def is_delta(self):
        if self.size <2:
            return False

        #right side
        a,b,c,d = self.columns[len(self.columns)-1]
        ap, bp, cp, dp = self.columns[len(self.columns)-2]
        first = self.delta_config(a,c,bp)
        revers = self.delta_config(d,b,cp)

        
        if revers:
            self.flip_config_right = self.flip_horizontal()
            self.is_right_flipped = True
            self.right_configuration = "d"

        if first:
            self.flip_config_right = self
            self.right_configuration = "d"
        
        #left side
        d, c, b, a = self.columns[0]
        dp,cp,bp,ap = self.columns[1]
        first = self.delta_config(a,c,bp)
        revers = self.delta_config(d,b,cp)
        
        if revers:
            self.flip_config_left = self.flip_vertical()
            fliped = self.flip_config_left
            self.left_configuration = "d"

        if first:
            self.flip_config_left = self.flip_vertical()
            #self.flip_config_left = fliped.flip_horizontal()
            self.is_left_flipped = True
            self.left_configuration = "d"
        

    def delta_config(self,a,c,bp):
        # a=bp !=0
        if(a.value == bp.value and a.value !=0):
            # c != a != 0
            if(c.value != a.value and c.value !=0):
                return True

    #particular case whene between two blocks
    # a==d, b==cd and c != a,b,0 and a != b and a,b,c != 0
    def is_pi(self):
        #right side
        

        if  self.end_col +2 < self.grid.width:

            a,b,c,d = self.columns[len(self.columns)-1]
            cd = self.grid.get_cell(self.end_col +2,2)

            if self.pi_config(a,b,c,d,cd):
                #print("Block4: Pi config 1")
                self.right_configuration = "p"
                self.flip_config_right = self
                self.pi_side = "left"
            

            d, c, b, a = self.columns[len(self.columns)-1]
            cd = self.grid.get_cell(self.end_col +2,1)
            if self.pi_config(a,b,c,d,cd):
                #print("Block4: Pi config 2")
                self.right_configuration = "p"
                self.flip_config_right = self.flip_horizontal()
                self.is_right_flipped = True
                self.pi_side = "left"
        
        #left side
        if self.start_col -2 >= 0:

            a,b,c,d = self.columns[0]
            cd = self.grid.get_cell(self.start_col -2,2)
            #print(f"Pi config A cd={cd.value}, a={a.value},b={b.value},c={c.value},d={d.value}")

            if self.pi_config(a,b,c,d,cd):
                #print("Block4: Pi config 3")
                #print("Block4: Pi config left t f")
                self.left_configuration = "p"
                self.is_left_flipped = False
                self.flip_config_left = self.flip_vertical()
                self.pi_side = "right"
            

            d, c, b, a = self.columns[0]
            cd = self.grid.get_cell(self.start_col -2,1)
            #print("Pi config B:",cd.value)
            if self.pi_config(a,b,c,d,cd):
                #print("Block4: Pi config 4")
                self.left_configuration = "p"
                fliped = self.flip_vertical()
                self.flip_config_left = fliped.flip_horizontal()
                self.is_left_flipped = True
                self.pi_side = "right"


    def pi_config(self,a,b,c,d,cd):
        # a==d, b==cd and c != a,b,0 and a != b and a,b,c != 0
        if a.value == d.value and b.value == cd.value :
            if c.value != a.value and c.value != b.value and c.value !=0 and a.value != b.value and a.value !=0 and b.value !=0:
                return True
        
        return False
    

    # In reverse of the paiper (j,1 j,2 j,3 j,4 => j,3 j,2 j,1 j,0) 
    # ONLY D' and D2' Have vertical sym
    # j,1 == j,3 == j+2,0 == j+2,2 != 0 
    # j+1,0 == j+1,1 == j+1,3 == j+2,1 == j+2,3 == 0
    # j+1,2 != 0 != j,1
    
    # particular config functions return list of tuples (config,j,is_fliped) 
    def get_Delta(self):
        #j = border col - 2

        if(len(self.columns) < 3): return []
        j = len(self.columns) - 3

        res = []

        # not fliped
        cell_c = [(j,1),(j,3),(j+2,0),(j+2,2)]
        cell_0 = [(j+1,0),(j+1,1),(j+1,3),(j+2,1),(j+2,3)]
        if self.same_value(cell_c) and self.columns[j][1].value !=0:
            if self.same_value(cell_0) and self.columns[j+1][0].value == 0 :
                if self.columns[j+1][2].value != 0 and self.columns[j][1].value != self.columns[j+1][2].value: 
                    self.particular_config_j = self.columns[j][0].y
                    res.append(("D",self.columns[j][0].y,False))

        # fliped
        cell_c = [(j,2),(j,0),(j+2,3),(j+2,1)]
        cell_0 = [(j+1,3),(j+1,2),(j+1,0),(j+2,2),(j+2,0)]
        if self.same_value(cell_c) and self.columns[j][2].value !=0:
            if self.same_value(cell_0) and self.columns[j+1][3].value == 0 :
                if self.columns[j+1][1].value != 0 and self.columns[j][2].value != self.columns[j+1][1].value: 
                    self.particular_config_j = self.columns[j][0].y
                    res.append(("D",j,True))

        #print("Block4: get_Delta res: ", res)
        return res


    # D' and D2' are only particular config with vertic sym
    # they have (config,j,hori,verti) w verti more

    # D' can appear multiple times so we return the list of j and if fliped

    #Is Delta'
    #j-1,1 == j,0 == j,3 == j+1,1 == j+2,3 == j+4,2 != 0
    #j-1,2 == j,1 == j,2 == j+1,0 == j+1,2 == j+1,3 == j+2,0 == j+2,1 == j+2,2 == 0

    def get_Delta_p(self):
        j_first = len(self.columns) - 4
        if (len(self.columns) < 5):
            return []
        
        # list of tuples (j,is_fliped) for each config found in the block
        res =[]
        #checking for the config starting from each column (to detect config in the middle)
        for j in range(j_first, 0, -1):
            cell_c = [(j-1,1),(j,0),(j,3),(j+1,1),(j+2,3),(j+3,2)]
            cell_0 = [(j-1,2),(j,1),(j,2),(j+1,0),(j+1,2),(j+1,3),(j+2,0),(j+2,1),(j+2,2)]
            if self.same_value(cell_c) and self.columns[j-1][1].value !=0:
                if self.same_value(cell_0) and self.columns[j-1][2].value == 0 : 
                    res.append(("D'",self.columns[j][0].y,False,False))
                    
        
        #check for horisontal fliped
        for j in range(j_first, 0, -1):
            cell_c = [(j-1,2),(j,3),(j,0),(j+1,2),(j+2,0),(j+3,1)]
            cell_0 = [(j-1,1),(j,2),(j,1),(j+1,3),(j+1,1),(j+1,0),(j+2,3),(j+2,2),(j+2,1)]
            if self.same_value(cell_c) and self.columns[j-1][2].value !=0:
                if self.same_value(cell_0) and self.columns[j-1][1].value == 0 : 
                    res.append(("D'",self.columns[j][0].y,True,False))

        # Check for vertical sym

        for j in range(0, len(self.columns)-2):
            cell_c = [(j+1,1),(j,0),(j,3),(j-1,1),(j-2,3),(j-3,2)]
            cell_0 = [(j+1,2),(j,1),(j,2),(j-1,0),(j-1,2),(j-1,3),(j-2,0),(j-2,1),(j-2,2)]
            if self.same_value(cell_c) and self.columns[j+1][1].value !=0:
                if self.same_value(cell_0) and self.columns[j+1][2].value == 0 : 
                    res.append(("D'",self.columns[j][0].y,False,True))
                    
        
        #check for horisontal fliped
        for j in range(1, len(self.columns)-3):
            cell_c = [(j+1,2),(j,3),(j,0),(j-1,2),(j-2,0),(j-3,1)]
            cell_0 = [(j+1,1),(j,2),(j,1),(j-1,3),(j-1,1),(j-1,0),(j-2,3),(j-2,2),(j-2,1)]
            if self.same_value(cell_c) and self.columns[j+1][2].value !=0:
                if self.same_value(cell_0) and self.columns[j+1][1].value == 0 : 
                    res.append(("D'",self.columns[j][0].y,True,True))


        return res


    # j-1,1 == j,0 == j,3 == j+1,1 == j+2,3 !=0
    # j+2,2 != 0 != j-1,1
    # j-1,2 == j,1 == j,2 == j+1,0 == j+1,2 == j+1,3 == 0
    def get_Delta_p2(self):
        j_max=len(self.columns) - 3
        if (len(self.columns) < 4):
            return []
        res = []
        for j in range(j_max, 0, -1): 
            cell_c = [(j-1,1),(j,0),(j,3),(j+1,1),(j+2,3)]
            cell_0 = [(j-1,2),(j,1),(j,2),(j+1,0),(j+1,2),(j+1,3)]
            if self.same_value(cell_c) and self.columns[j-1][1].value !=0:
                if self.same_value(cell_0) and self.columns[j-1][2].value == 0 and self.columns[j+2][2].value != 0 and self.columns[j-1][1].value != self.columns[j+2][2].value:
                    self.particular_config_j = self.columns[j][0].y
                    res.append(("D2'",self.columns[j][0].y,False,False))
        
        #check for horisontal fliped
        for j in range(j_max, 0, -1):
            cell_c = [(j-1,2),(j,3),(j,0),(j+1,2),(j+2,0)]
            cell_0 = [(j-1,1),(j,2),(j,1),(j+1,3),(j+1,1),(j+1,0)]
            if self.same_value(cell_c) and self.columns[j-1][2].value !=0:
                if self.same_value(cell_0) and self.columns[j-1][1].value == 0 and self.columns[j+2][1].value != 0 and self.columns[j-1][2].value != self.columns[j+2][1].value:
                    self.particular_config_j = self.columns[j][0].y
                    res.append(("D2'",self.columns[j][0].y,True,False))

        #check for vertical sym

        for j in range(1, len(self.columns)-2): 
            cell_c = [(j+1,1),(j,0),(j,3),(j-1,1),(j-2,3)]
            cell_0 = [(j+1,2),(j,1),(j,2),(j-1,0),(j-1,2),(j-1,3)]
            if self.same_value(cell_c) and self.columns[j+1][1].value !=0:
                if self.same_value(cell_0) and self.columns[j+1][2].value == 0 and self.columns[j-2][2].value != 0 and self.columns[j+1][1].value != self.columns[j-2][2].value:
                    self.particular_config_j = self.columns[j][0].y
                    res.append(("D2'",self.columns[j][0].y,False,True))
        
        #check for horisontal fliped
        for j in range(1, len(self.columns)-2):
            cell_c = [(j+1,2),(j,3),(j,0),(j-1,2),(j-2,0)]
            cell_0 = [(j+1,1),(j,2),(j,1),(j-1,3),(j-1,1),(j-1,0)]
            if self.same_value(cell_c) and self.columns[j+1][2].value !=0:
                if self.same_value(cell_0) and self.columns[j+1][1].value == 0 and self.columns[j-2][1].value != 0 and self.columns[j+1][2].value != self.columns[j-2][1].value:
                    self.particular_config_j = self.columns[j][0].y
                    res.append(("D2'",self.columns[j][0].y,True,True))


        return res


    #Lambda praticular case like pi
    #j-1 empty
    #j-2,0 == j-2,2 == j,1 == j,3 != 0
    #j-2,1 == j-2,3 == "j-1" == j,2 == 0
    #j,0 != j,1 =! j+1,2!= 0
    #j+1,2 != j,1 =! 0
    def get_Lambda(self):
        if self.size < 2:
             return []
        if(self.start_col -2 < 0):
            return []
        res = []

        cell_jm2_0 = self.grid.get_cell(self.start_col -2,0)
        cell_jm2_1 = self.grid.get_cell(self.start_col -2,1)
        cell_j_0 = self.columns[0][0]
        cell_jp1_2 = self.grid.get_cell(self.start_col +1,2)

        j = self.start_col
        cells_0 = [(j-2,1),(j-2,3),(j,2)]
        cells_c = [(j-2,0),(j-2,2),(j,1),(j,3)]

        if  self.same_value_grid(cells_c) and cell_jm2_0.value != 0:
            if self.same_value_grid(cells_0) and cell_jm2_1.value == 0:
                if(cell_j_0.value != cell_jm2_0.value and cell_j_0.value != 0):
                    if(cell_jp1_2.value != cell_jm2_0.value and cell_jp1_2.value != 0 and cell_jp1_2.value != cell_j_0.value):
                        #print("Block4: Lambda config")
                        #print(f"Block4: Lambda config j={j},{len(self.columns)}")
                        #self.particular_config_j = self.columns[j][0].y
                        self.particular_config_j = self.grid.get_cell(j,0).y
                        res.append(("L",j,False))
                        
        #check for horisontal fliped
        cell_jm2_3 = self.grid.get_cell(self.start_col -2,3)
        cell_jm2_2 = self.grid.get_cell(self.start_col -2,2)
        cell_j_3 = self.columns[0][3]
        cell_jp1_1 = self.grid.get_cell(self.start_col +1,1)

        cells_0 = [(j-2,2),(j-2,0),(j,1)]
        cells_c = [(j-2,3),(j-2,1),(j,2),(j,0)] 

        if self.same_value_grid(cells_c) and cell_jm2_3.value != 0:
            if self.same_value_grid(cells_0) and cell_jm2_2.value == 0:
                if(cell_j_3.value != cell_jm2_3.value and cell_j_3.value != 0):
                    if(cell_jp1_1.value != cell_jm2_3.value and cell_jp1_1.value != 0 and cell_jp1_1.value != cell_j_3.value):
                        res.append(("L",j,True))
        

        return res


    #j-2,0 == j-2,2 == j,1 == j,3 != 0
    #j-2,1 == j-2,3 == j,2 == j+1,1 == j+1,2 == j+1,3 == 0
    #j,0 != j,1 != 0
    #j+2,1 safe
    def get_Lambda_p(self):
        if self.size < 3:
            return []
        if (self.start_col -2 < 0):
            return []

        res = []

        j = self.start_col
        cells_c = [(j-2,0),(j-2,2),(j,1),(j,3)]
        cells_0 = [(j-2,1),(j-2,3),(j,2),(j+1,1),(j+1,2),(j+1,3)]
        cell_jm2_0 = self.grid.get_cell(self.start_col -2,0)
        cell_jm2_1 = self.grid.get_cell(self.start_col -2,1)
        cell_j_0 = self.columns[0][0]
        cell_jp2_1 = self.grid.get_cell(self.start_col +2,1)

        if self.same_value_grid(cells_c) and cell_jm2_0.value != 0:
            if self.same_value_grid(cells_0) and cell_jm2_1.value == 0:
                if(cell_j_0.value != cell_jm2_0.value and cell_j_0.value != 0):
                    if cell_jp2_1.is_safe:
                        #self.particular_config_j = self.gird.get_cell(j,0).y
                        res.append(("L'",j,False))

        #check for horisontal fliped
        cell_c = [(j-2,3),(j-2,1),(j,2),(j,0)]
        cell_0 = [(j-2,2),(j-2,0),(j,1),(j+1,2),(j+1,1),(j+1,0)]
        cell_jm2_3 = self.grid.get_cell(self.start_col -2,3)
        cell_jm2_2 = self.grid.get_cell(self.start_col -2,2)
        cell_j_3 = self.columns[0][3]
        cell_jp2_2 = self.grid.get_cell(self.start_col +2,2)

        if self.same_value_grid(cell_c) and cell_jm2_3.value != 0:
            if self.same_value_grid(cell_0) and cell_jm2_2.value == 0:
                if(cell_j_3.value != cell_jm2_3.value and cell_j_3.value != 0):
                    if cell_jp2_2.is_safe:
                        #print("Block4: Lambda' fliped config")
                        self.particular_config_j = self.grid.get_cell(j,3).y
                        res.append(("L'",j,True))
                    
        return res
    
    #same as Lambda but j-2,1 or j-2,3 colored and j-3 not empty
    def get_Lambda_2(self):
        if self.size < 2:
             return []
        if(self.start_col -3 < 0):
            return []
        res = []

        cell_jm2_0 = self.grid.get_cell(self.start_col -2,0)
        cell_j_2 = self.grid.get_cell(self.start_col ,2)
        cell_j_0 = self.columns[0][0]
        cell_jp1_2 = self.grid.get_cell(self.start_col +1,2)
        j = self.start_col
        cells_c = [(j-2,0),(j-2,2),(j,1),(j,3)]
        cells_jm3 = [(j-3,0),(j-3,1),(j-3,2),(j-3,3)]

        if  self.same_value_grid(cells_c) and cell_jm2_0.value != 0:
            if cell_j_2.value == 0:
                if(cell_j_0.value != cell_jm2_0.value and cell_j_0.value != 0):
                    if(cell_jp1_2.value != cell_jm2_0.value and cell_jp1_2.value != 0 and cell_jp1_2.value != cell_j_0.value):
                        #Check if j-3 not empty
                        if not(self.same_value_grid(cells_jm3)):
                            #check if j-2,1 or j-2,3 colored and other one empty
                            cell_jm2_3 = self.grid.get_cell(self.start_col -2,3)
                            cell_jm2_1 = self.grid.get_cell(self.start_col -2,1)
                            #print(f"Block4: Lambda2 check j-2,1={cell_jm2_1.value} j-2,3={cell_jm2_3.value}")
                            if (cell_jm2_1.value == 0 and cell_jm2_3.value != 0) or (cell_jm2_1.value != 0 and cell_jm2_3.value == 0):
                                #print("Block4: Lambda2 config")
                                #self.particular_config_j = self.columns[j][0].y
                                res.append(("L2",j,False))
        
        #check for horisontal fliped
        cell_jm2_3 = self.grid.get_cell(self.start_col -2,3)
        cell_j_1 = self.grid.get_cell(self.start_col ,1)
        cell_j_3 = self.columns[0][3]
        cell_jp1_1 = self.grid.get_cell(self.start_col +1,1)

        cells_c = [(j-2,3),(j-2,1),(j,2),(j,0)]
        cells_jm3 = [(j-3,3),(j-3,2),(j-3,1),(j-3,0)]
        if self.same_value_grid(cells_c) and cell_jm2_3.value != 0:
            if cell_j_1.value == 0:
                if(cell_j_3.value != cell_jm2_3.value and cell_j_3.value != 0):
                    if(cell_jp1_1.value != cell_jm2_3.value and cell_jp1_1.value != 0 and cell_jp1_1.value != cell_j_3.value):
                        #Check if j-3 not empty
                        if not(self.same_value_grid(cells_jm3)):
                            #check if j-2,2 or j-2,0 colored and other one empty
                            cell_jm2_0 = self.grid.get_cell(self.start_col -2,0)
                            cell_jm2_2 = self.grid.get_cell(self.start_col -2,2)
                            if (cell_jm2_2.value == 0 and cell_jm2_0.value != 0) or (cell_jm2_2.value != 0 and cell_jm2_0.value == 0):
                                print("Block4: Lambda2 fliped config")
                                #self.particular_config_j = self.columns[j][3].y
                                res.append(("L2",j,True))

        return res
    


    #same as Lambda' but j-2,1 or j-2,3 colored and j-3 not empty
    def get_Lambda_2_p(self):
        if self.size < 3:
            return []
        if (self.start_col -3 < 0):
            return []

        res = []
        j = self.start_col
        cells_c = [(j-2,0),(j-2,2),(j,1),(j,3)]
        cells_0 = [(j,2),(j+1,1),(j+1,2),(j+1,3)]
        cell_jm2_0 = self.grid.get_cell(self.start_col -2,0)
        cell_j_2 = self.grid.get_cell(self.start_col ,2)
        cell_j_0 = self.columns[0][0]
        cell_jp2_1 = self.grid.get_cell(self.start_col +2,1)
        
        cells_jm3 = [(j-3,0),(j-3,1),(j-3,2),(j-3,3)]

        if  self.same_value_grid(cells_c) and cell_jm2_0.value != 0:
            #print("Lambda_p: same value c")
            if self.same_value_grid(cells_0) and cell_j_2.value == 0:
                #print("Lambda_p: same value 0")
                if(cell_j_0.value != cell_jm2_0.value and cell_j_0.value != 0):
                    #print("Lambda_p: cell j,0 value")
                    if cell_jp2_1.is_safe:

                        #Check if j-3 not empty
                        if not(self.same_value_grid(cells_jm3)):
                            #check if j-2,1 or j-2,3 colored and other one empty
                            cell_jm2_3 = self.grid.get_cell(self.start_col -2,3)
                            cell_jm2_1 = self.grid.get_cell(self.start_col -2,1)
                            if (cell_jm2_1.value == 0 and cell_jm2_3.value != 0) or (cell_jm2_1.value != 0 and cell_jm2_3.value == 0):
                                #print("Block4: Lambda2' config")
                                self.particular_config_j = self.columns[j][0].y
                                res.append(("L2'",j,False))

        #check for horisontal fliped
        cell_c = [(j-2,3),(j-2,1),(j,2),(j,0)]
        cell_0 = [(j,1),(j+1,2),(j+1,1),(j+1,0)]
        cell_jm2_3 = self.grid.get_cell(self.start_col -2,3)
        cell_j_1 = self.grid.get_cell(self.start_col,1)
        cell_j_3 = self.columns[0][3]
        cell_jp2_2 = self.grid.get_cell(self.start_col +2,2)
        cells_jm3 = [(j-3,3),(j-3,2),(j-3,1),(j-3,0)]

        if self.same_value_grid(cell_c) and cell_jm2_3.value != 0:
            if self.same_value_grid(cell_0) and cell_j_1.value == 0:
                if(cell_j_3.value != cell_jm2_3.value and cell_j_3.value != 0):
                    if cell_jp2_2.is_safe:
                        #Check if j-3 not empty
                        if not(self.same_value_grid(cells_jm3)):
                            #check if j-2,2 or j-2,0 colored and other one empty
                            cell_jm2_0 = self.grid.get_cell(self.start_col -2,0)
                            cell_jm2_2 = self.grid.get_cell(self.start_col -2,2)
                            if (cell_jm2_2.value == 0 and cell_jm2_0.value != 0) or (cell_jm2_2.value != 0 and cell_jm2_0.value == 0):
                                print("Block4: Lambda2' fliped config")
                                self.particular_config_j = self.columns[j][3].y
                                res.append(("L2'",j,True))

        return res




    #set the left and right configurations of the block
    def check_configurations(self):

        
        self.left_configuration = None 
        self.right_configuration = None
        self.is_right_flipped = False
        self.is_left_flipped = False

        self.is_alpha()
        self.is_beta()
        self.is_gamma()
        self.is_delta()
        self.is_pi()

        """
        if self.end_col == self.grid.width - 1:
            self.right_configuration = None
            self.is_right_flipped = False

        if self.end_col == 0:
            if self.right_configuration == None:
                self.right_configuration = "b"
        """

        if self.end_col == 0:
            if self.right_configuration == None:
                self.right_configuration = "b"
        #manage particulars cases
        self.manage_particular_config()

        
        
        
    def print_info(self):
        print(f"\nBlock from column {self.start_col} to {self.end_col}, size: {self.size}")
        print(f"Left: {self.left_configuration} Right: {self.right_configuration}")
        print(f"particular config: {self.particular_config}")

    # managment of the particular config fliped or not
    def manage_particular_config(self):
        particular_configs = []
        Delta_conf = self.get_Delta()
        if Delta_conf != []:
            particular_configs.extend(Delta_conf)
        Delta_p_conf = self.get_Delta_p()
        if Delta_p_conf != []:
            particular_configs.extend(Delta_p_conf)
        Delta_p2_conf = self.get_Delta_p2()
        if Delta_p2_conf != []:
            particular_configs.extend(Delta_p2_conf)
        Lambda_conf = self.get_Lambda()
        if Lambda_conf != []:
            particular_configs.extend(Lambda_conf)
        Lambda_p_conf = self.get_Lambda_p()
        if Lambda_p_conf != []:
            particular_configs.extend(Lambda_p_conf)
        Lambda_2_conf = self.get_Lambda_2()
        if Lambda_2_conf != []:
            particular_configs.extend(Lambda_2_conf)
        Lambda_2_p_conf = self.get_Lambda_2_p()
        if Lambda_2_p_conf != []:
            particular_configs.extend(Lambda_2_p_conf)

        self.particular_configs = particular_configs
        
        #print(f"Block4: particular config {particular_configs}")

    #flip the block on horizontal axis 
    #goal is to apply same strategy after fliping (creating a new block object pointing to same cells)
    def flip_horizontal(self):
        flipped_block = Block(self.grid)
        flipped_block.start_col = self.start_col
        flipped_block.end_col = self.end_col
        flipped_block.size = self.size
        flipped_block.is_safe = self.is_safe
        flipped_block.is_sound = self.is_sound
        flipped_block.is_sick = self.is_sick

        #flip each column
        for col in self.columns:
            a,b,c,d = col
            flipped_col = [d,c,b,a]
            flipped_block.columns.append(flipped_col)

        #flip configurations
        flipped_block.left_configuration = self.left_configuration
        flipped_block.right_configuration = self.right_configuration
        return flipped_block
        
    def flip_vertical(self):
        flipped_block = Block(self.grid)
        flipped_block.start_col = self.start_col
        flipped_block.end_col = self.end_col
        flipped_block.size = self.size
        flipped_block.is_safe = self.is_safe
        flipped_block.is_sound = self.is_sound
        flipped_block.is_sick = self.is_sick

        #flip columns order
        for i in range(self.size-1,-1,-1):
            col = self.columns[i]
            flipped_block.columns.append(col)

        return flipped_block



    def print_block(self,block=None):
        if block == None:
            block = self

        print(f"Block Start:{block.start_col} End: {block.end_col}, size: {block.size} Left: {block.left_configuration} Right: {block.right_configuration}")
        print("left:", block.left_configuration,"vertical flip:", block.is_left_flipped, "horizontal flip:", block.is_left_flipped)
        
        print("right:", block.right_configuration,"vertical flip:", block.is_right_flipped, "horizontal flip:", block.is_right_flipped)
        for i in range(4):
            for col in block.columns:
                cell = col[i]
                print(f"{cell.value} ", end="")
            print()
        print()
        print(block.particular_config)


    #check if all cells in list have same value and is not the val "not_val"
    #list = [(j,x)]
    def same_value(self,list):
        (j,x) = list[0]
        first_value = self.columns[j][x].value
        for j,x in list: 
            if self.columns[j][x].value != first_value: 
                return False
        return True
    
    #same function as above but on the grid
    def same_value_grid(self,list):
        (j,x) = list[0]
        first_value = self.grid.get_cell(j,x).value
        for j,x in list: 
            if self.grid.get_cell(j,x).value != first_value: 
                return False
        return True