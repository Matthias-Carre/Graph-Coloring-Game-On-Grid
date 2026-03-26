import tkinter as tk
from graphic.Draw import Draw

class Interface:
    def __init__(self,root,engine):
        self.root = root
        self.engine = engine
        self.grid = engine.grid
        self.canvas = None
        self.on_click = engine.on_click
        self.draw = None
        self.selected_color = engine.color_selected
        engine.on_update_callback = self.draw_grid
        


    
    def create_window(self):
        #remove previous widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        window_height = self.engine.window_height 
        window_width = self.engine.window_width

        if(window_height / window_width > self.grid.height/self.grid.width):
            ratio = window_width / self.grid.width
            
        else:
            ratio = window_height / self.grid.height
            

        #set the window size to match the gird of the graph
        #ratio = min(window_width / self.grid.width, window_height / self.grid.height)
        w = ratio * self.grid.width
        h = ratio * self.grid.height
        print(f"h={h}, ratio={ratio}, grid height={self.grid.height}, window height={window_height}")
        self.root.geometry(f'{int(w)}x{int(h)+45+28*self.grid.num_colors}') 

        print(f"Window size: {int(w)}x{int(h)}, ratio: {ratio}")
        canvas = tk.Canvas(self.root, width=w, height=h, bg="white")
        self.canvas = canvas

        draw = Draw( window_width,window_height, self.grid,self.root,canvas)
        self.draw = draw

        draw.draw_window()
        self.draw_grid()
        #creation of the canvas and button/color selection
        canvas.bind("<Button-1>", self.on_click)
        self.engine.color_var_accessor = draw.color_selected

        self.draw_buttons()

        playing = True
        


    def get_draw(self):
        return self.draw
    
    #draw the grid
    def draw_grid(self):
        self.draw.draw_grid()
    
    #create and draw a button with text and command
    def draw_button(self, text, command):
        print("DrawButtonInterface")
        self.draw.draw_button(text, command)
        self.root.update()
    
    #draw all buttons needed for the game interface
    def draw_buttons(self):
        #self.draw_button("test",self.test_print())
        return 

    def test_print(self,msg=""):
        print("InterTestPrint:",msg)

    def show_popup(self, title, message, popup_type="error"):
        """Affiche un message popup directement sur le canvas
        popup_type: 'error' (rouge), 'warning' (jaune), 'info' (bleu)
        """
        colors = {
            "error": {"bg": "#ffcccc", "border": "#ff0000", "text": "#cc0000"},
            "warning": {"bg": "#fff3cd", "border": "#ffc107", "text": "#856404"},
            "info": {"bg": "#cce5ff", "border": "#007bff", "text": "#004085"}
        }
        color = colors.get(popup_type, colors["error"])
        
        # Position centrale du canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 10:  # Canvas pas encore rendu
            canvas_width = 800
            canvas_height = 600
        
        cx, cy = canvas_width // 2, canvas_height // 2
        box_width, box_height = 300, 80
        
        # Créer le rectangle de fond
        popup_rect = self.canvas.create_rectangle(
            cx - box_width // 2, cy - box_height // 2,
            cx + box_width // 2, cy + box_height // 2,
            fill=color["bg"], outline=color["border"], width=3, tags="popup"
        )
        
        # Créer le titre
        popup_title = self.canvas.create_text(
            cx, cy - 15,
            text=title, font=("Arial", 12, "bold"),
            fill=color["text"], tags="popup"
        )
        
        # Créer le message
        popup_message = self.canvas.create_text(
            cx, cy + 10,
            text=message, font=("Arial", 10),
            fill=color["text"], tags="popup"
        )
        
        # Supprimer le popup après 2 secondes
        self.root.after(500, lambda: self.canvas.delete("popup"))