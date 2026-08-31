from game.Grid import Grid
import argparse
from game.Bob.bob import Bob
from game.Alice.alice import Alice

def run_random_vs_random(grid_width, grid_height, num_colors, num_games):
    #create the grid:
    grid = Grid(grid_height, grid_width, num_colors)

    alice = Alice(grid)
    bob = Bob(grid)

    Alice_win=0
    Bob_win=0

    Alice_kill_herself=0
    Bob_kill_Alice=0
    colored_cell_proportion_list = []

    for game in range(num_games):
        start = True
        grid = Grid(grid_height, grid_width, num_colors)
        alice = Alice(grid)
        bob = Bob(grid)
        while True:
            grid.player = 0

            # Alice logic
            #alice_move = alice.next_safe_move()
            alice_move = alice.next_random_move()
            #alice_move = alice.next_heuristic1_move()

            if start:
                start = False
                alice_move = (2,2,1)

            if alice_move is None:
                continue
            x,y,col = alice_move
            grid.play_move(x, y, col)
            
            if is_grid_full(grid):
                
                Alice_win += 1
                break
            if has_uncolorable_cell(grid):
                Bob_win += 1
                Alice_kill_herself += 1
                break


            grid.player = 1

            # BOB logic here
            bob_move = bob.next_random_move()
            #bob_move = bob.kill_if_possible()
            #bob_move = bob.next_move_euristic()


            if bob_move is None:
                break

            x,y,col = bob_move
            grid.play_move(x, y, col)
            if is_grid_full(grid):
                Alice_win += 1
                break
            if has_uncolorable_cell(grid):
                #show the grid
                #print("BOB win:")
                #render(grid)
                #print(f"------")                
                Bob_win += 1
                Bob_kill_Alice += 1
                break

        colored_cell_proportion_list.append(grid.proportion_colored_cells())
        '''
        if game % 1000 == 0:
            print(f"Game {game}/{num_games}")
            render(grid)
        '''
         
    print(f"On {num_games} games with grid {grid_width}x{grid_height} and {num_colors} colors:")
    print(f"Alice wins: {Alice_win} ({100*Alice_win/num_games:.1f}%)")
    print(f"Bob wins:   {Bob_win} ({100*Bob_win/num_games:.1f}%)")
    print(f"Alice kills herself: {Alice_kill_herself} ({100*Alice_kill_herself/num_games:.1f}%)")
    print(f"Bob kills Alice: {Bob_kill_Alice} ({100*Bob_kill_Alice/num_games:.1f}%)") 
    avg_colored_proportion = sum(colored_cell_proportion_list) / len(colored_cell_proportion_list)
    print(f"Average proportion of colored cells at game end: {avg_colored_proportion}") 
    print(f"-==-=--=-=-=-=-==---=--=-=")

# Alice Random vs Bob Random
# with input size, color and number of games to simulate
def main():
    parser = argparse.ArgumentParser(
        description="Run random-vs-random graph coloring matches and report win rates."
    )
    parser.add_argument("--w", type=int, default=4, help="Grid width.")
    parser.add_argument("--h", type=int, default=4, help="Grid height.")
    parser.add_argument("--colors", type=int, default=4, help="Number of colors.")
    parser.add_argument("--games", type=int, default=100, help="Number of games to simulate.")
    
    args = parser.parse_args()

    #run_random_vs_random(args.w, args.h, args.colors, args.games)

    for e in [4,5,6,10,20] :
        run_random_vs_random(e, e, 4, 5000)

    # get random move from alice




def render(grid):
    """Displays current grid state in terminal."""
    player_color = {
        0: "\033[91m",
        1: "\033[94m",
    }
    reset = "\033[0m"
        
    # Iterate row by row
    first_row = ""
    for i in range(grid.width):
        first_row += f"{i} "
    print(f"  {first_row}")

    for j in range(grid.height):
        row_str = f"{j:2} "
        for i in range(grid.width):
            cell = grid.get_cell(i, j)
            val = cell.get_value()

            if val == 0:
                row_str += ". "
                continue

            color = player_color.get(cell.played_by, "")
            row_str += f"{color}{val}{reset} "
        print(row_str)
    print("===================")

def is_grid_full(grid):
    for j in range(grid.height):
        for i in range(grid.width):
            if grid.get_cell(i, j).get_value() == 0:
                return False
    return True

def has_uncolorable_cell(grid):
    for j in range(grid.height):
        for i in range(grid.width):
            cell = grid.get_cell(i, j)
            if cell.is_uncolorable:
                return True
    return False

if __name__ == "__main__":
    main()