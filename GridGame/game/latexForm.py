"""
This file contains the logic for generating LaTeX code to represent the grid in the GridGame.

Could be usedfull to generate a latex representation of the grid to write a paper or to visualize the grid in a more formal way.
"""


# input : gird
# out : latex code for the grid
def save_grid_latex(grid, filename="grid_output.tex"):

    # start of the latex code
    latex_code = r"""
\begin{figure}
\begin{center}
\centering
\begin{minipage}[c]{0.48\textwidth}
\scalebox{1}{
\begin{tikzpicture}[scale=0.5,inner sep=0.7mm]
"""
    width = grid.width
    height = grid.height

    # draw the grid
    latex_code += "        \\foreach \\y in {0,...," + str(height - 1) + "} {\n"
    latex_code += "        \\foreach \\x in {0,...," + str(width - 1) + "} {\n"
    latex_code += "                \\draw [draw=black, line width=1pt] (\\x,\\y) rectangle (\\x+1,\\y+1);\n"
    latex_code += "        }\n"
    latex_code += "        }\n\n"

    # add the values (1->c1 ...)
    for y in range(height-1, -1, -1):
        for x in range(width):
            cell = grid.get_cell(x, y)
            value = cell.get_value()
            if value != 0:
                inverted_y = height - 1 - y
                latex_code += f"        \\node at ({x + 0.5},{inverted_y + 0.5}){{\\footnotesize $c_{{{value}}}$}};\n"

    # sides values
    latex_code += "        \\foreach \\x in {0,...," + str(width - 1) + "} {\n"
    latex_code += "            \\node at (\\x+0.5," + str(height + 0.5) + "){{\\footnotesize $\\x$}};\n"
    latex_code += "        }\n"


    latex_code += "        \\foreach \\y in {0,...," + str(height - 1) + "} {\n"
    latex_code += "            \\node at (-0.5,\\y+0.5){{\\footnotesize $\\y$}};\n"
    latex_code += "        }\n"

    #blackout "any" cells
    for y in range(height-1,-1,-1):
        for x in range(width):
            cell = grid.get_cell(x, y)
            if cell.any_color:  # Si la cellule a le tag any_color
                inverted_y = height - 1 - y
                latex_code += f"        \\draw [draw=black, line width=1pt, fill=gray] ({x},{inverted_y}) rectangle ({x+1},{inverted_y+1});\n"


    # end part of latex 
    latex_code += r"""
\end{tikzpicture}
}
\end{minipage}
\caption{TITRE A AJOUTER}
\label{fig:NOMFIGURE}
\end{center}
\end{figure}
"""
    save_latex_to_file(latex_code, filename)
    return latex_code

# input :  string text, string filename
# out : void
def save_latex_to_file(latex_code, filename="grid_output.tex"):
    #folder of latex files
    path = "latex_files/"
    
    try:
        with open(path+filename, "w") as file:
            file.write(latex_code)
        print(f"Le code LaTeX a été sauvegardé dans le fichier '{path+filename}'.")
    except Exception as e:
        print(f"Une erreur s'est produite lors de la sauvegarde : {e}")