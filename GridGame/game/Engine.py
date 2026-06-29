import sys
import importlib.util
from pathlib import Path
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
        # NN / mode selection
        self.bob_mode = "heuristic"   # "random" | "heuristic" | "nn"
        self.alice_mode = "heuristic" # "random" | "heuristic" | "nn"
        self.bob_nn = None
        self.alice_nn = None
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
        self.window.draw_button("print blocks",self.print_blocks)
        self.window.draw_button("Reset",self.reset)
        self.window.draw_button("Bob: Heuristic", self.toggle_bob_mode, name="bob_mode_btn")
        self.window.draw_button("Alice: Heuristic", self.toggle_alice_mode, name="alice_mode_btn")
        self._try_load_nn_models()

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
        #print("key pressed",event)
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

        if event.char == 'a':
            self.alice_move()
        if event.char == 'b':
            self.bob_move()
        
        
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
        if self.alice_mode == "random":
            move = self.Alice.next_random_move()
        elif self.alice_mode == "nn" and self.alice_nn is not None:
            move = self._nn_move(self.alice_nn)
        else:  # heuristic
            move = self.Alice.next_euristic1_move()
        if move is None:
            move = self.Alice.next_random_move()
        x, y, color = move
        print(f"Alice move ({self.alice_mode}): {x}, {y}, color: {color}")
        self.change_node_color(self.grid, x, y, color)
        self.on_update_callback()

        if self.strategy is not None:
            self.strategy.check_induction_hypothesis()
    """
    check if it's Bob's turn
    If yes, play the move coresponding to Bob's strategy
    """
    def bob_move(self):
        if self.grid.player != 1:
            print("Not Bob's turn")
            return
        if self.bob_mode == "random":
            move = self.Bob.next_random_move()
        elif self.bob_mode == "nn" and self.bob_nn is not None:
            move = self._nn_move(self.bob_nn)
        else:  # heuristic
            move = self.Bob.next_move_euristic()
        if move is None:
            move = self.Bob.next_random_move()
        x, y, color = move
        print(f"Bob move ({self.bob_mode}): {x}, {y}, color: {color}")
        self.change_node_color(self.grid, x, y, color)
        self.on_update_callback()

    """
    Undo the last move played
    """
    def undo(self):
        print(f"====----====\nUndo last move")
        if(self.grid.undo_move()):
            #self.on_update_callback()
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
        #keep the status of the cell before the move to update the strategy if needed
        cell = grid.get_cell(x,y)

        #che
        if len(cell.patients) > 0 and len(cell.patients[0].doctors) > 0:
            is_doc = True
            patient = cell.patients[0]
            other_doc = patient.doctors[0] if patient.doctors[0].x != cell.x else patient.doctors[1]

            #print("other doc: ", other_doc.x, other_doc.y)
        else:
            is_doc = False
            patient = None
            other_doc = None
        status_before_move = "safe" if cell.is_safe else "sound" if cell.is_sound else ""

        #check if the move is valid
        if(not(grid.play_move(x, y, color))):
           return 
        if self.strategy is not None:
            self.strategy.move_played(x, y, color, "A" if grid.player == 0 else "B",is_doc, status_before_move, patient, other_doc)

        if self.grid.player == 1:
            self.grid.round += 1
        self.grid.player = 0 if self.grid.player == 1 else 1

        self.grid.recompute_local_status(x, y, distance=2)


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

    """
    show or hide states of the cells
    """
    def toggle_debug(self):
        self.window.draw.print_status = not self.window.draw.print_status
        self.on_update_callback()

    """
    show or hide the number of rounds
    """
    def toggle_rounds(self):
        self.window.draw.print_rounds = not self.window.draw.print_rounds
        self.on_update_callback()

    def print_blocks(self):
        for block in self.grid.blocks.blocks:
            print("Block:")
            block.print_block()

    # ------------------------------------------------------------------
    # Mode selection: random / heuristic / nn
    # ------------------------------------------------------------------
    _BOB_MODES = ["random", "heuristic", "nn"]
    _ALICE_MODES = ["random", "heuristic", "nn"]
    _MODE_LABELS = {"random": "Random", "heuristic": "Heuristic", "nn": "NN"}

    def toggle_bob_mode(self):
        idx = self._BOB_MODES.index(self.bob_mode)
        self.bob_mode = self._BOB_MODES[(idx + 1) % len(self._BOB_MODES)]
        if self.bob_mode == "nn" and self.bob_nn is None:
            print("Bob NN not loaded — falling back to heuristic")
        label = f"Bob: {self._MODE_LABELS[self.bob_mode]}"
        self.window.update_button_text("bob_mode_btn", label)
        print(f"Bob mode → {self.bob_mode}")

    def toggle_alice_mode(self):
        idx = self._ALICE_MODES.index(self.alice_mode)
        self.alice_mode = self._ALICE_MODES[(idx + 1) % len(self._ALICE_MODES)]
        if self.alice_mode == "nn" and self.alice_nn is None:
            print("Alice NN not loaded — falling back to heuristic")
        label = f"Alice: {self._MODE_LABELS[self.alice_mode]}"
        self.window.update_button_text("alice_mode_btn", label)
        print(f"Alice mode → {self.alice_mode}")

    # ------------------------------------------------------------------
    # NN helpers
    # ------------------------------------------------------------------
    def _try_load_nn_models(self):
        """Tente de charger les modèles NN de Bob et Alice depuis les checkpoints."""
        base = Path(__file__).parent.parent  # GridGame/

        # --- Bob ---
        bob_ckpt = base / "checkpoints" / "Bob" / "latest.pt"
        if bob_ckpt.exists():
            try:
                import torch
                spec = importlib.util.spec_from_file_location(
                    "BobModel", str(base / "rl_Bob" / "Model.py")
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self.bob_nn = mod.GraphColoringNet(
                    width=self.grid.width,
                    height=self.grid.height,
                    num_colors=self.grid.num_colors,
                )
                ckpt = torch.load(str(bob_ckpt), map_location="cpu")
                self.bob_nn.load_state_dict(ckpt["model_state_dict"])
                self.bob_nn.eval()
                print(f"Bob NN chargé depuis {bob_ckpt}")
            except Exception as e:
                print(f"Impossible de charger le NN de Bob : {e}")
                self.bob_nn = None
        else:
            print(f"Checkpoint Bob introuvable : {bob_ckpt}")

        # --- Alice ---
        alice_ckpt = base / "checkpoints" / "Alice" / "latest.pt"
        if alice_ckpt.exists():
            try:
                import torch
                spec = importlib.util.spec_from_file_location(
                    "AliceModel", str(base / "rl_Alice" / "Model.py")
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self.alice_nn = mod.GraphColoringNet(
                    width=self.grid.width,
                    height=self.grid.height,
                    num_colors=self.grid.num_colors,
                )
                ckpt = torch.load(str(alice_ckpt), map_location="cpu")
                self.alice_nn.load_state_dict(ckpt["model_state_dict"])
                self.alice_nn.eval()
                print(f"Alice NN chargée depuis {alice_ckpt}")
            except Exception as e:
                print(f"Impossible de charger le NN d'Alice : {e}")
                self.alice_nn = None
        else:
            print(f"Checkpoint Alice introuvable : {alice_ckpt}")

    def _get_obs_for_nn(self):
        """Construit l'observation (grille + masque d'actions légales) pour le NN."""
        import numpy as np
        num_colors = self.grid.num_colors
        height = self.grid.height
        width = self.grid.width
        obs = np.zeros((num_colors + 1, height, width), dtype=np.float32)
        for i in range(width):
            for j in range(height):
                val = self.grid.get_cell(i, j).get_value()
                obs[val, j, i] = 1.0
        total_actions = width * height * num_colors
        mask = np.zeros(total_actions, dtype=bool)
        for i in range(width):
            for j in range(height):
                if self.grid.get_cell(i, j).get_value() == 0:
                    for c in range(num_colors):
                        if self.grid.is_move_valid(i, j, c + 1):
                            mask[(j * width + i) * num_colors + c] = True
        return {"observation": obs, "mask": mask}

    def _nn_move(self, nn_model):
        """Calcule le coup du NN et retourne (x, y, color)."""
        import torch
        obs = self._get_obs_for_nn()
        obs_t = torch.tensor(obs["observation"], dtype=torch.float32).unsqueeze(0)
        mask_t = torch.tensor(obs["mask"], dtype=torch.bool).unsqueeze(0)
        with torch.no_grad():
            logits, _ = nn_model(obs_t)
            logits = logits.masked_fill(~mask_t, -1e8)
            best = torch.argmax(logits, dim=1).item()
        num_colors = self.grid.num_colors
        width = self.grid.width
        c = (best % num_colors) + 1
        cell_idx = best // num_colors
        x = cell_idx % width
        y = cell_idx // width
        return x, y, c