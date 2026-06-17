from game.Bob.strategy_3 import *
from game.Bob.strategy_random import *

class Bob:
    def __init__(self,grid):
        self.grid = grid
        self.strategy = []
        self.load_strategy()



    def load_strategy(self):

        if self.grid.height == 3 and self.grid.num_colors == 3:
            self.strategy = [
                (has_color_critical,winning_move),
                (has_diagonal,solve_diagonal),
                (is_side,solve_side),
                (is_center,solve_center)
            ]
        else:
            self.strategy = [
                (is_any,euristic_move),
                (is_any,random_move)
            ]

    # Bob create cc vertex and make it uncolorable if excist
    def next_move_euristic(self):
        if self.grid.player != 1:
            print("Not Bob's turn")
            return None
        return euristic_move(self.grid,self.grid.last_moves[-1] if self.grid.last_moves else None)
        
        

    def next_move(self):
        if self.grid.player != 1:
            print("Not Bob's turn")
            return None
        #print("\n===-- Bob move --===")
        
        last_move = self.grid.last_moves[-1] if self.grid.last_moves else None
        ax, ay, acolor = last_move

        for is_case, solve_case in self.strategy:
            if is_case(self.grid,last_move):
                return solve_case(self.grid,last_move)
        
        print("Bob: no strategy found, play random")
        return random_move(self.grid,last_move)

    def next_random_move(self):

        return random_move(self.grid,self.grid.last_moves[-1] if self.grid.last_moves else None)