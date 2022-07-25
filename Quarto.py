# -*- coding: utf-8 -*-

import copy
from os import access
from plistlib import InvalidFileException
import threading
import numpy as np
import enum
import time
import random


class Node:
    def __init__(self, state, next_move=None, id=0, ):
        self.id = id
        self.action = next_move
        self.parent: Node = None
        self.child_list: list[Node] = []
        self.state: Quarto = state
        self.visited = False
        self.won_games = 0.0
        self.games = 0.0
        self.win_ratio = 0.0

    def new_parent(self, parent):
        self.parent = parent

    def new_child(self, child):
        self.child_list.append(child)

    def calculate_wins(self):
        self.win_ratio = self.won_games / self.games if self.games > 0 else 0


# METODO A IMPLEMENTAR
# PSEUDOCODIGO
""" while(current_time < time_limit)
        while(has_finished() == false)
        if(haSidoExploradoAntes)
            crearNumeroAleatorio
            if(numeroAleatorio > exploitation)
                mejorEstadoConocido
        else(noHaSidoExplorado || numeroAleatorio < exploitation)
            accionAlAzar 
            if(noHaSidoVisitado)
                agregarArbol
        if(esEstadoFinal)
            backPropagation
"""


def mcts(root, time_limit=2, exploitation=0.5):
    tree_root = Node(root)
    time_start = time.time()
    while(time.time() - time_start < time_limit):
        actual_node = tree_root
        while(actual_node.state.has_finished() == False):
            random_number = random.random()
            if(actual_node.visited == True):
                if(random_number > exploitation):
                    actual_node = best_known_state(actual_node)
            else:
                actual_node.visited = True
                actual_node = node_expansion(actual_node)
        actual_node.games += 1
        if(actual_node.state.get_winner() == 1):
            actual_node.won_games += 1
        actual_node.calculate_wins()
        while(tree_root != actual_node):
            actual_node.parent.games += actual_node.games
            actual_node.parent.won_games += actual_node.won_games
            actual_node = actual_node.parent
            actual_node.calculate_wins()
    actual_node = tree_root
    actual_node = best_known_state(actual_node)
    return actual_node.action


def node_expansion(node: Node):
    possible_actions = node.state.get_available_actions()
    random_id = int(random.randrange(0, len(possible_actions), 1))
    action = possible_actions[random_id]
    leaf = Node(node.state.do_action(action), action, random_id)
    for index in node.child_list:
        if index.id == leaf.id:
            return index
    leaf.new_parent(node)
    node.new_child(leaf)
    return leaf


def best_known_state(actual_node: Node):
    b_child, b_prob = 0, 0
    for index in range(len(actual_node.child_list)):
        if(actual_node.child_list[index].win_ratio > b_prob):
            b_child = index
            b_prob = actual_node.child_list[index].win_ratio
    return actual_node.child_list[b_child]

### DO NOT EDIT ###


try:
    import tkinter as tk
except ImportError:
    try:
        import Tkinter as tk
    except ImportError:
        print("Unsupported library: Tkinter, please install")

# Globals
FPS = 24

# Piece properties


class Properties(enum.IntFlag):
    DARK = 0x1  # 1
    LIGHT = 0x2  # 2
    SHORT = 0x4  # 4
    TALL = 0x8  # 8
    HOLLOW = 0x10  # 16
    FLAT = 0x20  # 32
    CIRCLE = 0x40  # 64
    SQUARE = 0x80  # 128

# Game phases


class QuartoPhase(enum.IntEnum):
    CHOOSE_PIECE = 1
    CHOOSE_SPACE = 2
    FINISHED = 3

# Game class


class Quarto():
    def __init__(self):
        self.reset()

    def copy(self):
        new_state = copy.copy(self)
        new_state.pieces = copy.copy(self.pieces)
        new_state.spaces = copy.copy(self.spaces)
        new_state.board = self.board.copy()
        return new_state

    def reset(self):
        self.pieces = []
        self.spaces = [(i, j) for i in range(4) for j in range(4)]
        for i in range(16):
            piece = (Properties.LIGHT if i & 0x1 else Properties.DARK) \
                | (Properties.TALL if i & 0x2 else Properties.SHORT) \
                | (Properties.FLAT if i & 0x4 else Properties.HOLLOW) \
                | (Properties.SQUARE if i & 0x8 else Properties.CIRCLE)
            self.pieces.append(piece)
        self.board = np.zeros((4, 4), dtype=np.uint8)
        self.phase = QuartoPhase.CHOOSE_PIECE
        self.player = int(random.random()*2)
        self.chosen_piece = None
        self.winner = -1

    def turn_player(self):
        return self.player == 0

    def turn_ai(self):
        return self.player == 1

    def has_finished(self):
        return self.phase == QuartoPhase.FINISHED

    def get_winner(self):
        return self.winner

    def get_available_actions(self):
        if self.phase == QuartoPhase.CHOOSE_PIECE:
            return self.pieces
        elif self.phase == QuartoPhase.CHOOSE_SPACE:
            return self.spaces
        return []

    def do_action(self, action):
        new_state = self
        if self.phase == QuartoPhase.CHOOSE_PIECE:
            if not action in self.pieces:
                return self
            new_state = copy.copy(self)
            new_state.pieces = [
                piece for piece in self.pieces if piece != action]
            new_state.phase = QuartoPhase.CHOOSE_SPACE
            new_state.player = (new_state.player + 1) % 2
            new_state.chosen_piece = action
        elif self.phase == QuartoPhase.CHOOSE_SPACE:
            if not action in self.spaces:
                return self
            new_state = copy.copy(self)
            new_state.board = self.board.copy()
            new_state.spaces = [
                space for space in self.spaces if space != action]
            new_state.phase = QuartoPhase.CHOOSE_PIECE
            new_state.board[action] = new_state.chosen_piece
            new_state.chosen_piece = None
            new_state._check_victory()
        return new_state

    def _check_victory(self):
        fin = np.any(np.bitwise_and.reduce(self.board, axis=0)) or \
            np.any(np.bitwise_and.reduce(self.board, axis=1)) or \
            ((self.board[0, 0] & self.board[1, 1] & self.board[2, 2] & self.board[3, 3]) > 0) or \
            ((self.board[3, 0] & self.board[2, 1] &
             self.board[1, 2] & self.board[0, 3]) > 0)
        if fin:
            self.winner = self.player
            self.phase = QuartoPhase.FINISHED
        elif (len(self.pieces) == 0 and self.chosen_piece == None):
            self.phase = QuartoPhase.FINISHED


def random_action(env):
    time.sleep(3)
    return random.choice(env.get_available_actions())


class mainWindow():
    def __init__(self, aiAction=random_action):
        self.map_seed = random.randint(0, 65535)
        self.quarto = Quarto()
        # Control
        self.ai = aiAction
        self.redraw = False
        self.ready = False
        self.running = False
        self.action = None
        self.last_action = 0
        self.game_thread = threading.Thread(target=self.game_loop, daemon=True)
        self.game_lock = threading.Lock()
        # Interface
        self.root = tk.Tk()
        self.root.title("Quarto MCTS AI")
        self.root.bind("<Configure>", self.resizing_event)
        self.root.bind("<Button-1>", self.click_event)
        self.frame = tk.Frame(self.root, width=700, height=550)
        self.frame.pack()
        self.canvas = tk.Canvas(self.frame, width=1, height=1)
        # Control buttons
        self.buttonReset = tk.Button(
            self.frame, text="Reset", command=self.reset, bg="indian red")
        self.stringPhase = tk.StringVar(value="Phase: LOADING")
        self.labelPhase = tk.Label(
            self.frame, textvariable=self.stringPhase, relief=tk.RIDGE, padx=5, pady=2)
        self.stringPlayer = tk.StringVar(value="Player: LOADING")
        self.labelPlayer = tk.Label(
            self.frame, textvariable=self.stringPlayer, relief=tk.RIDGE, padx=5, pady=2)
        self.stringAction = tk.StringVar(value="WAIT")
        self.labelAction = tk.Label(
            self.frame, textvariable=self.stringAction, relief=tk.RIDGE, pady=5, padx=10)
        # Start
        self.game_thread.start()
        self.root.after(0, self.update_loop)
        self.root.mainloop()

    # Update loop
    def update_loop(self):
        if time.time()-self.last_action >= 0.75:
            if self.running:
                txt = (self.stringAction.get(
                )+'.') if self.stringAction.get().startswith("Waiting") else "Waiting for the AI"
                self.stringAction.set(
                    txt[:-6] if txt.endswith('......') else txt)
            self.last_action = time.time()
        if self.redraw and self.ready:
            self.redraw_canvas()
        self.root.after(int(1000/FPS), self.update_loop)

    # Resizing event
    def resizing_event(self, event):
        if event.widget == self.root:
            self.redraw = True
            self.canvas_width = max(event.width - 40, 1)
            self.canvas_height = max(event.height - 80, 1)
            self.frame.configure(width=event.width, height=event.height)
            self.canvas.configure(width=self.canvas_width,
                                  height=self.canvas_height)
            self.canvas.place(x=20, y=20)
            # Control buttons
            self.buttonReset.place(
                x=event.width-70, y=event.height-40, width=50)
            self.labelPhase.place(x=20, y=event.height-55)
            self.labelPlayer.place(x=20, y=event.height-30)
            self.labelAction.place(x=200, y=event.height-50, width=300)
            self.ready = True

    # Click event
    def click_event(self, event):
        if not self.quarto.player:
            if self.quarto.phase == QuartoPhase.CHOOSE_SPACE:
                row_cell = int((event.y - self.board_offset_y)//self.cell_size)
                col_cell = int((event.x - self.board_offset_x)//self.cell_size)
                if row_cell >= 0 and row_cell < 4 and col_cell >= 0 and col_cell < 4:
                    self.action = (row_cell, col_cell)
            elif self.quarto.phase == QuartoPhase.CHOOSE_PIECE:
                piece = int((event.x - self.piece_offset_x - 10) //
                            self.piece_size)
                if event.y >= self.piece_offset_y and event.y <= (self.piece_offset_y + self.piece_size) and piece >= 0 and piece < len(self.quarto.pieces):
                    self.action = self.quarto.pieces[piece]

    # Game loop (run on a separate thread)
    def game_loop(self):
        while not self.ready:
            time.sleep(0.05)
        self.update_labels()
        while True:
            if self.quarto.phase == QuartoPhase.FINISHED:
                time.sleep(0.1)
                continue
            if self.quarto.turn_ai():
                self.running = True
                action = self.ai(self.quarto)
                self.running = False
                if action:
                    with self.game_lock:
                        self.quarto = self.quarto.do_action(action)
                    self.update_labels()
                    continue
            elif self.action:
                with self.game_lock:
                    self.quarto = self.quarto.do_action(self.action)
                    self.action = None
                    self.update_labels()
                    continue
            time.sleep(0.05)

    # Updates messages
    def update_labels(self):
        self.stringPhase.set("Phase: "+self.quarto.phase.name)
        self.stringPlayer.set(
            "Player: " + ("AI" if self.quarto.player else "Human"))
        if self.quarto.phase == QuartoPhase.CHOOSE_PIECE:
            self.stringAction.set("Choose the piece to give to the AI")
        elif self.quarto.phase == QuartoPhase.CHOOSE_SPACE:
            self.stringAction.set(
                "Choose the space for the highlightened piece")
        elif self.quarto.phase == QuartoPhase.FINISHED:
            self.stringAction.set(
                "Winner: " + ("AI" if self.quarto.player else "Human"))
        self.redraw = True

    # Reset board
    def reset(self):
        with self.game_lock:
            self.quarto.reset()
            self.redraw = True

    # Draw piece method
    def draw_piece(self, piece, x, y, size):
        color = "#E9E9E9" if piece & Properties.LIGHT else "#404040"
        method = self.canvas.create_rectangle if piece & Properties.SQUARE else self.canvas.create_oval
        offset = min(5, 5*size/80)
        real_size = size - offset
        method(x+offset, y+offset, x+real_size,
               y+real_size, fill=color, width=2)
        if piece & Properties.TALL:
            soffset = min(10, 10*size/80)
            method(x+offset+soffset, y+offset+soffset, x+real_size -
                   soffset, y+real_size-soffset, fill=color, width=2)
        if piece & Properties.HOLLOW:
            hoffset = min(20, 20*size/80)
            self.canvas.create_oval(x+offset+hoffset, y+offset+hoffset, x +
                                    real_size-hoffset, y+real_size-hoffset, fill="#000000", width=0)

    # Redraw method
    def redraw_canvas(self):
        npieces = len(self.quarto.pieces)
        dh = min(80, 80*self.canvas_height/400)
        pad = min(20, 20*self.canvas_height/400)
        self.dh, self.pad = dh, pad
        self.board_size = min(self.canvas_width, self.canvas_height-(dh+pad))
        self.board_offset_x, self.board_offset_y = (
            self.canvas_width - self.board_size)//2, (self.canvas_height - dh - self.board_size)//2
        self.canvas.delete("all")
        self.canvas.create_rectangle(
            0, 0, self.canvas_width, self.canvas_height-dh, fill="#606060", width=0)
        self.canvas.create_rectangle(
            0, self.canvas_height-dh, self.canvas_width, self.canvas_height, fill="#925A3D", width=0)
        self.canvas.create_rectangle(self.board_offset_x, self.board_offset_y, self.board_offset_x +
                                     self.board_size, self.board_offset_y + self.board_size, fill="#B97A57", width=2)
        self.cell_size = self.board_size/4
        cell_offset = min(10, 10*self.board_size/400)
        # Draw remaining pieces
        if self.quarto.chosen_piece:
            npieces += 1
        self.piece_size = min(dh, (self.canvas_width - 20)/npieces)
        self.piece_offset_x = (self.canvas_width - 20 -
                               (npieces*self.piece_size))/2
        self.piece_offset_y = self.canvas_height - \
            dh + (dh - self.piece_size)/2
        for i, piece in enumerate(self.quarto.pieces):
            self.draw_piece(piece, self.piece_offset_x + (i*self.piece_size) +
                            10, self.piece_offset_y, self.piece_size)
        # Draw chosen piece
        if self.quarto.chosen_piece:
            self.canvas.create_rectangle(self.piece_offset_x + (self.piece_size*(npieces-1)) + 10, self.canvas_height -
                                         self.dh, self.piece_offset_x + (self.piece_size*npieces) + 10, self.canvas_height, width=0, fill="#67412C")
            self.draw_piece(self.quarto.chosen_piece, self.piece_offset_x + (
                self.piece_size*(npieces-1)) + 10, self.piece_offset_y, self.piece_size)
        # Draw board pieces
        for i in range(4):
            for j in range(4):
                if self.quarto.board[i, j]:
                    self.draw_piece(self.quarto.board[i, j], self.board_offset_x + j*self.cell_size + cell_offset,
                                    self.board_offset_y + i*self.cell_size + cell_offset, self.cell_size - 2*cell_offset)
        # Draw hard lines
        self.canvas.create_line(
            0, self.canvas_height-dh, self.canvas_width, self.canvas_height-dh, width=2)
        for i in range(1, 4):
            delta = i*self.cell_size
            self.canvas.create_line(self.board_offset_x, self.board_offset_y + delta,
                                    self.board_offset_x + self.board_size, self.board_offset_y + delta, width=2)
            self.canvas.create_line(self.board_offset_x + delta, self.board_offset_y,
                                    self.board_offset_x + delta, self.board_offset_y + self.board_size, width=2)
        self.redraw = False


if __name__ == "__main__":
    # Modify call: use custom AI function
    x = mainWindow(aiAction=mcts)
