from game.GameState import GameState
from graphic.Interface import Interface
from game.strategy.block_height_4 import BlockHeight4
from game.latexForm import save_grid_latex

class GameEngine:
    def __init__(self,grid,root,Alice=None,Bob=None):
        self.window_width = 1600
        self.window_height = 800
        self.grid = grid
        self.root = root
        self.state = GameState(grid)
        self.strategy = None

        self.Alice = Alice
        self.Bob = Bob
        self.on_click = self.on_left_click
        self.color_selected = 1
        self.on_update_callback = None
        self.buttons={}
        self.window = Interface(root,self)

        self.reset = None
        # for latex file
        self.num_latex = 0 
        

    def button_test(self):
        print("Test")


    """
    create the window and start the game
    """
    def run(self):
        if self.grid.height == 4:
            self.strategy = BlockHeight4(self.grid)
            self.grid.blocks = self.strategy


        self.window.create_window()
        self.window.root.title(f"Grid Game {self.grid.height}x{self.grid.width}")

        #management of inputs
        self.window.draw_button("Alice move",self.alice_move)
        self.window.draw_button("Bob move",self.bob_move)
        
       # self.window.draw_button("preview",self.preview)
        self.window.draw_button("Undo",self.undo)
        self.window.draw_button("debug",self.toggle_debug)
        self.window.draw_button("rounds",self.toggle_rounds)
        self.window.draw_button("Reset",self.reset)

        self.window.canvas.bind("<Button-1>", self.on_left_click)
        
        #press Button3 in the cell to draw "any" just to do ilustration (press again to remove)
        self.window.canvas.bind("<Button-3>", self.on_right_click)
        

        self.window.canvas.bind("<Button-2>",self.on_x_press)
        self.window.canvas.bind("<Key>", self.on_key_press)
        self.window.canvas.focus_set()

        
        """
        current_player = self.Alice
        move = current_player.get_move()
        if move is not None:
            x, y, color = move
            self.grid.play_cell(x, y, color, player=current_player.name)
            # Switch to the other player
            current_player = self.Bob if current_player == self.Alice else self.Alice
        """

        self.root.mainloop()

    """
    input : event of a click/key press
    out : do the action corresponding to the click/key press
        u : undo
        l : save the grid in a latex file
        1-5 : select the color
    """
    def on_key_press(self,event):
        print("key pressed",event)
        if event.char == 'u':
            self.undo()
        if event.char == 'l':
            self.num_latex += 1
            save_grid_latex(self.grid,f"grid_{self.num_latex}.tex")
        #color selection
        if event.char == '1':
            self.color_selected = 0
            self.color_var_accessor.set(0)

        if event.char == '2':
            self.color_selected = 1
            self.color_var_accessor.set(1)

        if event.char == '3':
            self.color_selected = 2
            self.color_var_accessor.set(2)

        if event.char == '4':
            self.color_selected = 3
            self.color_var_accessor.set(3)

        if event.char == '5':
            self.color_selected = 4
            self.color_var_accessor.set(4)
        
        
    """
    input : event of a click
    out : on left click try to play the move at the current position
    """
    def on_left_click(self,event):
        
        #print("click",event)
        x = event.x
        y = event.y
        ratio = min(self.window_width / self.grid.width, self.window_height / self.grid.height)
        i = int(x // ratio)
        j = int(y // ratio)

        if hasattr(self, 'color_var_accessor'):
            self.color_selected = self.color_var_accessor.get()
            #print("color selected:", self.color_selected)

        if (0 <= i) and (i < self.grid.width) and (0 <= j) and (j < self.grid.height) and (self.color_selected != -1):
            print(f'=-=-=-=-=-=-=-=-=-=-=\nButton clicked at: {i}, {j}, color: {self.color_selected}')
            if not(self.is_move_valid(i, j, self.color_selected + 1)):
                print("Engie: Invalid move")
                #popup message
                self.window.show_popup("Invalid Move", "The selected move is not valid.")
                
                return
            
            if (self.grid.get_cell(i, j).get_value() == 0):
                #entry point of the move
                self.change_node_color(self.grid, i, j, self.color_selected + 1)
                self.on_update_callback()
    
    """
    input : event of a click
    out : on right click print the cell informations
    """
    def on_right_click(self,event):
        #print("right click",event)
        x = event.x
        y = event.y
        ratio = min(self.window_width / self.grid.width, self.window_height / self.grid.height)
        i = int(x // ratio)
        j = int(y // ratio)

        if (0 <= i) and (i < self.grid.width) and (0 <= j) and (j < self.grid.height):
            print(f'Right Button clicked at: {i}, {j}')
            cell = self.grid.get_cell(i, j)
            cell.print_cell_informations()
        
        self.on_update_callback()
    
    """
    idea: show what would be play in advance and see how it change depending on the next move
    """
    def preview(self):
        print("Previewing next move")
        
    """
    input : event of a click
    out : on middle click, play "any" in the cell just to do ilustration
    """
    def on_x_press(self,event):
        #print("button3 pressed",event)
        x = event.x
        y = event.y
        ratio = min(self.window_width / self.grid.width, self.window_height / self.grid.height)
        i = int(x // ratio)
        j = int(y // ratio)

        cell = self.grid.get_cell(i, j)
        cell.any_color = not cell.any_color

            
        self.on_update_callback()

    #manage Alice actions
    """
    check if it's Alice's turn
    If yes, play the move coresponding to Alice's strategy
    """
    def alice_move(self):
        if self.grid.player != 0:
            print("Not Alice's turn")
            return
        x, y, color = self.Alice.next_move()  
        self.change_node_color(self.grid, x, y, color)
        self.on_update_callback()

    """
    check if it's Bob's turn
    If yes, play the move coresponding to Bob's strategy
    """
    def bob_move(self):
        if self.grid.player != 1:
            print("Not Bob's turn")
            return
        x, y, color = self.Bob.next_move()
        self.change_node_color(self.grid, x, y, color)
        self.on_update_callback()

    """
    Undo the last move played
    """
    def undo(self):
        print(f"====----====\nUndo last move")
        if(self.grid.undo_move()):
            self.on_update_callback()
            if self.strategy is not None:
                #self.strategy.update_all_blocks()
                self.strategy.rebuild_from_grid()
                self.grid.blocks = self.strategy


            if self.grid.player == 0:
                self.grid.round -= 1
            self.grid.player = 0 if self.grid.player == 1 else 1
        self.on_update_callback()
        return
    

    #input void
    #out close the window and lunch again
    def reset(self):
        self.reset(self.tk_root) if self.reset is not None else print("No reset function defined")

    """
    input : 
        grid : gird of the game
        x,y : position of the move
        color : color of the move
    out : void
    result : play the move on the grid and update the interface

    """
    def change_node_color(self,grid, x, y, color):

        if(not(grid.play_move(x, y, color))):
           return 
        if self.strategy is not None:
            self.strategy.move_played(x, y, color, "A" if grid.player == 0 else "B")

        if self.grid.player == 1:
            self.grid.round += 1
        self.grid.player = 0 if self.grid.player == 1 else 1
        return
    
    """
    call the draw function
    """
    def draw_grid(self):
        self.window.draw_grid()

    """
    check if the move is valid
    """
    def is_move_valid(self,x,y,color):
        return self.grid.is_move_valid(x,y,color)
    
    
    def test_print(self,msg):
        print("EngineTestPrint:",msg)

    def toggle_debug(self):
        self.window.draw.print_status = not self.window.draw.print_status
        self.on_update_callback()

    def toggle_rounds(self):
        self.window.draw.print_rounds = not self.window.draw.print_rounds
        self.on_update_callback()