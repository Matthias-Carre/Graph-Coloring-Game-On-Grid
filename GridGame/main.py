import tkinter as tk
from game.Grid import Grid
from graphic.Draw import Draw
from game.Engine import GameEngine
from graphic.Interface import Interface
from game.Bob.bob import Bob
from game.Alice.alice import Alice




# input : root window, width of the grid, height of the grid, number of colors
# out : create the game and start it
def create_game(root,width=15, height=4,num_colors=4):
    #grid = Grid(width, height, num_colors=4)
    
    #for the cas of the paper
    #grid = Grid(3,16,4)
    grid = Grid(height, width, num_colors)

    engine = GameEngine(grid,root,Alice=Alice(grid),Bob=Bob(grid))
    engine.reset = lambda: reset_game(root)  # Set the reset function to call reset_game
  
    
    print("Game created with grid size:", width, "x", height)
    engine.run()


#function to reset the game
#input : root window
#out : new game
def reset_game(tk_root):
    # Clear the current game state and reset the interface
    tk_root.destroy()  # Close the current window
    main()


#create the window and ask the parameters of the game to create the game

def main():
    # Create the main window
    root = tk.Tk()
    root.title("Lunch Menu")
    
    main_frame = tk.Frame(root)
    main_frame.pack(padx=20, pady=20)

    # parameters selection
    tk.Label(root, text="Options:").pack(pady=10)

    main_frame = tk.Frame(root)
    main_frame.pack(padx=20, pady=20)
    tk.Label(main_frame, text="Largeur de la grille:").pack(pady=2.5)
    tk.Label(main_frame, text="(min 2,max 30):").pack(pady=3) 
    width_entry = tk.Entry(main_frame)
    width_entry.pack(pady=5)

    tk.Label(main_frame, text="Hauteur de la grille:").pack(pady=2.5)
    tk.Label(main_frame, text="(min 2,max 30):").pack(pady=3)
    height_entry = tk.Entry(main_frame)
    height_entry.pack(pady=5)

    tk.Label(main_frame, text="Nombre de couleurs").pack(pady=2.5)
    tk.Label(main_frame, text="(min 2,max 5):").pack(pady=3)
    color_entry = tk.Entry(main_frame)
    color_entry.pack(pady=5)

    # Submit button
    def submit():
        # need to check if input are int
        width = int(width_entry.get())
        if width < 2:
            width = 2
        elif width > 30:
            width = 30

        height = int(height_entry.get())
        if height < 2:
            height = 2
        elif height > 30:
            height = 30

        num_colors = int(color_entry.get())
        print(f"lunch with width: {width}, height: {height}")
        if num_colors < 2:
            num_colors = 2
        elif num_colors > 5:
            num_colors = 5
        create_game(root,width, height, num_colors)

    tk.Button(main_frame, text="Valider", command=submit).pack(pady=10)

    tk.mainloop()

if __name__ == "__main__":
    #selection des parametres
    #main()

    #Commenter au dessus et decommenter en dessous pour passer la selection des parametres
    create_game(tk.Tk(),width=20, height=4, num_colors=4)