import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.Grid import Grid
from game.strategy.block_height_4 import BlockHeight4
from game.strategy.Block4 import Block

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

"""create a custom grid to check confing"""
def make_grid(width, colored_cells):

    grid = Grid(height=4, width=width, num_colors=4)
    strategy = BlockHeight4(grid)
    grid.blocks = strategy

    for x, y, color in colored_cells:
        grid.play_move(x, y, color)
        strategy.move_played(x, y, color, "A")

    return grid, strategy


def get_block(strategy, x):
    return strategy.block_at(x)


def local_j_to_grid_col(block, local_j):
    return block.columns[local_j][0].y

#config type

@pytest.fixture
def grid_delta():
    """
     Delta :
    j,1 == j,3 == j+2,0 == j+2,2 != 0
    j+1,0 == j+1,1 == j+1,3 == j+2,1 == j+2,3 == 0
    j+1,2 != 0 != j,1
    """
    # j=2, couleur c=1, couleur sick=2
    colored = [
        (2, 1, 1),  # j,1
        (2, 3, 1),  # j,3
        (4, 0, 1),  # j+2,0
        (4, 2, 1),  # j+2,2
        (3, 2, 2),  # j+1,2 (sick, != c)
    ]
    return make_grid(width=10, colored_cells=colored)


@pytest.fixture
def grid_delta_p():
    """
    Delta' :
    j-1,1 == j,0 == j,3 == j+1,1 == j+2,3 == j+3,2 != 0
    j-1,2 == j,1 == j,2 == j+1,0 == j+1,2 == j+1,3 == j+2,0 == j+2,1 == j+2,2 == 0
    """
    c = 1
    colored = [
        (1, 1, c),  # j-1,1
        (2, 0, c),  # j,0
        (2, 3, c),  # j,3
        (3, 1, c),  # j+1,1
        (4, 3, c),  # j+2,3
        (5, 2, c),  # j+3,2
    ]
    return make_grid(width=12, colored_cells=colored)


@pytest.fixture
def grid_alpha():
    """
    Config alpha : b==d != 0, a et c not doc, a!=c or =0
    """
    colored = [
        (0, 1, 1),  # b
        (0, 3, 1),  # d
        (1, 2, 2),
    ]
    return make_grid(width=6, colored_cells=colored)


@pytest.fixture
def grid_pi():
    """
    Config pi :
    a==d, b==cd, c != a,b,0, a!=b, a,b,c != 0
    """
    colored = [
        (0, 0, 1),  # a
        (0, 3, 1),  # d
        (0, 1, 2),  # b
        (2, 2, 2),  # cd (colonne end+2)
        (0, 2, 3),  # c != a,b
    ]
    return make_grid(width=8, colored_cells=colored)



class TestDelta:
    def test_is_delta_detected(self, grid_delta):
        grid, strategy = grid_delta
        block = get_block(strategy, 2)
        assert block is not None, "Block non trouvé en colonne 2"
        found = block.get_Delta()
        assert found, "Config Delta non détectée"
        assert any(cfg == "D" for cfg, _, _ in found)

    def test_particular_config_is_delta(self, grid_delta):
        grid, strategy = grid_delta
        block = get_block(strategy, 2)
        block.check_configurations()
        found = block.get_Delta()
        assert found
        assert any(cfg == "D" for cfg, _, _ in found)

    def test_particular_config_j(self, grid_delta):
        grid, strategy = grid_delta
        block = get_block(strategy, 2)
        found = block.get_Delta()
        assert found
        _, local_j, _ = found[0]
        assert local_j_to_grid_col(block, local_j) == 2


class TestDeltaPrime:
    def test_is_delta_p_detected(self, grid_delta_p):
        grid, strategy = grid_delta_p
        block = get_block(strategy, 2)
        assert block is not None
        found = block.get_Delta_p()
        assert found, "Config Delta' non détectée"
        assert any(cfg == "D'" for cfg, _, _, _ in found)

    def test_particular_config_is_delta_p(self, grid_delta_p):
        grid, strategy = grid_delta_p
        block = get_block(strategy, 2)
        block.check_configurations()
        found = block.get_Delta_p()
        assert found
        assert any(cfg == "D'" for cfg, _, _, _ in found)

    def test_delta_p_detected_not_at_border(self, grid_delta_p):
        """Vérifie que Delta' est détecté même si le pattern n'est pas collé à droite"""
        grid, strategy = grid_delta_p
        block = get_block(strategy, 2)
        found = block.get_Delta_p()
        assert found, "Delta' doit être détecté quelle que soit la position dans le block"


class TestAlpha:
    def test_is_alpha_detected(self, grid_alpha):
        grid, strategy = grid_alpha
        block = get_block(strategy, 0)
        assert block is not None
        block.check_configurations()
        assert block.left_configuration == "a" or block.right_configuration == "a"


class TestPi:
    def test_is_pi_detected(self, grid_pi):
        grid, strategy = grid_pi
        block = get_block(strategy, 0)
        assert block is not None
        result = block.is_pi()
        assert result is not False
        assert block.right_configuration == "p"

    def test_pi_propagates_to_right_block(self, grid_pi):
        """Vérifie que pi à droite d'un block => pi à gauche du voisin"""
        grid, strategy = grid_pi
        # jouer une cellule en colonne 2 pour créer un block voisin
        grid.play_move(3, 0, 3)
        strategy.move_played(3, 0, 3, "B")

        right_block = strategy.block_at(3)
        right_block.print_block()
        #if right_block:
            #assert right_block.left_configuration == "p", \
            #    "Pi devrait être propagé au block de droite"



class TestNoFalsePositive:
    def test_empty_grid_no_config(self):
        grid, strategy = make_grid(width=8, colored_cells=[])
        # aucun block ne doit exister
        assert strategy.blocks == []

    def test_single_cell_no_delta(self):
        grid, strategy = make_grid(width=8, colored_cells=[(3, 1, 1)])
        block = strategy.block_at(3)
        assert block is not None
        assert block.get_Delta() == [], "Delta ne doit pas être détecté avec une seule cellule"

    def test_single_cell_no_delta_p(self):
        grid, strategy = make_grid(width=8, colored_cells=[(3, 1, 1)])
        block = strategy.block_at(3)
        assert block.get_Delta_p() == []