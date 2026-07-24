"""
This file contains the implementation of the Draw class, which is responsible for rendering the GridGame using the Tkinter library.
The Draw class provides methods for drawing the game grid, cells, and other graphical elements, as well as handling user interactions through buttons and radio buttons.
"""

import tkinter as tk

class Draw:
    def __init__(self, width, height, grid,root,canvas):
        self.width = width
        self.height = height
        self.grid = grid
        self.canvas = canvas
        self.number_of_colors = grid.num_colors
        self.colors = ["Red", "Green", "Blue","Purple"]
        self.color_selected = -1 # given by the radio button
        self.root = root
        self.turn = 0 #0 for Alice, 1 for Bob
        self.print_status = False
        self.print_rounds = True
        self.round = 1 
        self.cell_ratio = 1.0
        self.origin_x = 0.0
        self.origin_y = 0.0
        self.grid_pixel_width = 0.0
        self.grid_pixel_height = 0.0
        self.button_frame =  tk.Frame(self.root)
        self.button_frame.pack(pady=10)

    #draw text at x,y with color and font
    def draw_text(self, x, y, text, color="black", font=("Arial", 16)):
        self.canvas.create_text(x, y, text=text, fill=color, font=font)

    #draw rectangle form x,y to x+width,y+height
    def draw_rectangle(self, x, y, width, height, color):
        self.canvas.create_rectangle(x, y, x + width, y + height, fill=color, outline="")

    #draw circle centered in x,y with radius
    def draw_circle(self, x, y, radius, color):
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline="")
        self.canvas.create_oval(x - radius/1.5, y - radius/1.5, x + radius/1.5, y + radius/1.5, fill="white", outline="")

    def undo_last_move():
        return

    def bob_play():
        return
    
    def test_print(self,msg=""):
        print("DrawTestPrint:", msg)
        return

    #draw the color selection radio buttons
    def draw_color_selection(self):
        self.draw_color_selection_value()

    def draw_color_selection_value(self):
        color_frame = tk.Frame(self.root)
        color_frame.pack(anchor="w")
        radio_frame = tk.Frame(color_frame)
        radio_frame.pack(side="left")
        
        #color Slecetion
        for i in range(self.number_of_colors):
            tk.Radiobutton(radio_frame, text=(i+1), value=i, variable=self.color_selected).pack(anchor="w")
        button_frame = tk.Frame(color_frame)
        button_frame.pack(side="left", padx=10)
        #tk.Button(button_frame, text="random move", command=self.test_print).pack()

    #function to draw a button with text and command
    def draw_button(self, text, command):
        button = tk.Button(self.button_frame, text=text, command=command)
        button.pack(side="left", padx=5)
        return button

    #change to select another style of grid drawing 
    def draw_grid(self):
        #self.draw_gridV1()
        self.draw_gridV2()


    #draw the grid on the canvas with circles
    def draw_gridV1(self):
        ratio = min(self.width / self.grid.width, self.height / self.grid.height)
        for i in range(self.grid.width):
            for j in range(self.grid.height):
                x = i * ratio
                y = j * ratio
                cell = self.grid.get_cell(i, j)
                self.draw_circle(x + ratio / 2, y + ratio / 2, ratio / 2 - 5, self.colors[cell.get_value() - 1] if cell.get_value() > 0 else "black")
                player=cell.get_player()
                if(cell.is_uncolorable):
                    self.draw_text(x + ratio / 2, y + ratio / 2, "X", color="red", font=("Arial", 16))
                else:
                    self.draw_text(x + ratio / 2, y + ratio / 2, player, color="black", font=("Arial", 16))
                if(self.print_status):
                    self.draw_text(x + ratio / 2, y + ratio / 2 + 10, cell.get_status(), color="blue", font=("Arial", 8))

    #draw the grid on the canvas as we do on the paper
    def draw_gridV2(self):
        self.width = self.canvas.winfo_width()
        self.height = self.canvas.winfo_height()
        if self.width <= 1 or self.height <= 1:
            return

        ratio = min(self.width / self.grid.width, self.height / self.grid.height)
        self.cell_ratio = ratio
        self.grid_pixel_width = ratio * self.grid.width
        self.grid_pixel_height = ratio * self.grid.height
        self.origin_x = (self.width - self.grid_pixel_width) / 2
        self.origin_y = (self.height - self.grid_pixel_height) / 2

        self.draw_rectangle(0, 0, self.width, self.height, "white")

        # Draw a complete centered grid to avoid stretching the last row/column.
        for i in range(self.grid.width + 1):
            x = self.origin_x + i * ratio
            self.draw_rectangle(x, self.origin_y, 1, self.grid_pixel_height, "black")

        for j in range(self.grid.height + 1):
            y = self.origin_y + j * ratio
            self.draw_rectangle(self.origin_x, y, self.grid_pixel_width, 1, "black")

        cell_font = max(8, int(ratio / 1.5))
        for i in range(self.grid.width):
            for j in range(self.grid.height):
                x = self.origin_x + i * ratio
                y = self.origin_y + j * ratio
                cell = self.grid.get_cell(i, j)
                self.draw_text(x + ratio / 2, y + ratio / 2, cell.get_value() if cell.get_value()!=0 else "", "Blue" if cell.played_by == 1 else "Red", font=("Arial", cell_font))
                self.draw_text(x + ratio / 2, y + ratio / 2, "X" if cell.is_uncolorable else "", "black", font=("Arial", cell_font))
                if(self.print_status):
                    state = cell.get_status()
                    self.draw_text(x + ratio / 6, y + ratio / 6, state, color="green", font=("Arial", 8))
                
                    self.draw_doctor_patient(cell)

                if(self.print_rounds):
                    self.draw_text(x + ratio / 1.2, y + ratio / 1.2, cell.round, color="black", font=("Arial", 8))

                if(cell.any_color):
                    self.draw_text(x + ratio / 4, y + ratio / 4, "any", color="black", font=("Arial", 16))


    def draw_doctor_patient(self,cell):
        return
        """
        for patient in cell.patients:
            #draw a line from doctor to patient 
            ratio = min(self.width / self.grid.width, self.height / self.grid.height)
            x1 = cell.x * ratio + ratio / 2
            y1 = cell.y * ratio + ratio / 2
            x2 = patient.x * ratio + ratio / 2
            y2 = patient.y * ratio + ratio / 2
            self.canvas.create_line(y1, x1, y2, x2, fill="black", width=2, dash=(4, 2))
        """
        

    def draw_window(self):

        #creation of the canvas and button/color selection
        self.color_selected = tk.IntVar(value=0)
        self.canvas.pack()
        self.draw_gridV2()
        self.draw_color_selection()
        
