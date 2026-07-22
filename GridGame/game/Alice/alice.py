from game.Alice.strategy_3 import *
from game.Alice.strategy_4 import *
from game.Alice.strategy_random import *
from game.Alice.strategy_survive import *
from game.Alice.heuristic1 import *

CustomStrat = True
DEBUG = False

#Alice class that will play the game using a strategy based on the grid size and the last move of Bob


class Alice:
    def __init__(self,grid):
        self.grid = grid
        self.strategy = []
        self.load_strategy()


    #import the strategy depending on the grid size
    def load_strategy(self):
        if self.grid.height == 3 and self.grid.num_colors == 4:
            print("Alice: load strategy for 3*3 grid with 4 colors")
            self.strategy = [
                (is_side, solve_side),
                (is_other, solve_other)

                #(is_center, solve_center)
            ]
        elif self.grid.height == 4 and self.grid.num_colors == 4:

            #Strategy for 4*n based on "The Graph Coloring Game on 4 * n-Grids" C. Brosse, N. Martins, N. Nisse, R. Sampaio 
            self.strategy = [
                #(is_TEST, solve_TEST),

                #Case 1:
                (is_1_Delta, solve_1_Delta),
                (is_1_Dp_1, solve_1_Dp_1),
                (is_1_L, solve_1_L),
                (is_1_Dp_2, solve_1_Dp_2),
                (is_1_L,solve_1_L),
                (is_1_Lp, solve_1_Lp),
                (is_1_doc, solve_1_doc),
                (is_1_g_doc, solve_1_g_doc),
                (is_1_safe, solve_1_safe),
                
                #Case 2:
                (is_2_delta, solve_2_delta),
                (is_2_abgF, solve_2_abgF),
                (is_2_beta, solve_2_beta),
                (is_2_gamma, solve_2_gamma),
                (is_2_alpha, solve_2_alpha),
                (is_2_aplha_prime, solve_2_alpha_prime),

                #Case 3:
                (is_3_new, solve_3_new),
                (is_3_pi, solve_3_pi),
                (is_3_delta, solve_3_delta),
                (is_3_alpha_F, solve_3_alpha_F),
                (is_3_beta_F, solve_3_beta_F),
                (is_3_gamma_F, solve_3_gamma_F),
                (is_3_gamma, solve_3_gamma),
                (is_3_beta, solve_3_beta),
                (is_3_alpha, solve_3_alpha),

                (is_TestConfig,solve_TestConfig)
            ]
        else:
            self.strategy = [
                (is_any,heurisitic_move)
            ]

    #return a random valid move (x,y,color) for Alice
    def next_random_move(self):
        #print("Alice: random move")
        return random_move(self.grid, self.grid.last_Bob_move)

    #return a valide move (x,y,color) for Alice that will not create a color critical vertex for Bob
    def next_safe_move(self):
        #print("Alice: safe move")
        return survive_strategy(self.grid, self.grid.last_Bob_move)

    #return a valide move (x,y,color) for Alice base on heuristic
    def next_heuristic1_move(self):
        next_move = heurisitic_move(self.grid, self.grid.last_Bob_move)
        return next_move
        
        
    #return (x,y,color) of the move that Alice wants to play
    def next_move(self):
        if self.grid.player != 0:
            print("Not Alice's turn")
            return None
        #print("\n===-- Alice move --===")

        # react to Bob's last move
        
        #first move
        if(self.grid.round == 1):
            self.grid.round += 1
            return (0,1,1)
            
        
        #For custom strategy:


        #if CustomStrategy:
        #    self.next_euristic_move(self.grid, self.grid.last_Bob_move)
        
        if DEBUG:
            print("Alice strategy: Bob: ", self.grid.bob_play_on_config)
        for is_case, solve_case in self.strategy:
            if is_case(self.grid,self.grid.last_Bob_move):
                if DEBUG:
                    print(f"Return Alice: {solve_case(self.grid,self.grid.last_Bob_move)}")
                return solve_case(self.grid,self.grid.last_Bob_move)

        #case test:
        if is_TestConfig(self.grid,self.grid.last_Bob_move):
            return solve_TestConfig(self.grid,self.grid.last_Bob_move)
       

        #CASE 1: in block/border d/j,j-1 of L,L2,L',L'2/j-2 of L,L'/j-2 of L2,L'2 if j-3 not empty

        #case 1D


        #case 1D'

        #case 1L

        #case 1L'

        #case 1-doc

        #case 1g-doc

        #case 1-safe
        #!!!

        #Case 2: In Border not in D,L,L'

        #case 2d

        #case 2afgFree

        #case 2b

        #case 2g

        #case 2a

        #case 2a'


        #Case 3: empty col not in j-1 of L,L2,L',L'2

        #case 3new

        #case 3pi

        #case 3d

        #case 3aF

        #case 3bF

        #case 3gF

        #case 3g

        #case 3b

        #case 3a

    #cases:

    '''
    def handle_case_1D():
        bob_move = self.grid.last_Bob_move
        self.case_1D(bob_move)
    '''



