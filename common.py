#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from collections import defaultdict
from random import choice


@dataclass
class Puzzle:
    nb_move: int
    grid: str
    nb_state: int
    index: int
    over: int = 0

    def get_elements(self):
        """
        Run at use time, as it would be time consumming to run for each
        puzzle when loading the db.
        """
        elements = defaultdict(list)
        nb_wall = 0
        for i, c in enumerate(self.grid):
            if c != 'o':
                if c == 'x':
                    nb_wall += 1
                    c = 'x' + str(nb_wall)
                elements[c].append(i)
        return elements


def load_db(filepath):
    """
    Return a list of all Puzzle elements read in the file
    """
    print(f'[Load] Creating database from {filepath}')
    puzzles = []
    current_move = 0
    current_index = 0
    max_by_moves = {}

    f = open(filepath, 'r')
    for line in f.readlines():
        nb_move, grid, nb_state = line.split()
        nb_move = int(nb_move)
        if nb_move != current_move:
            max_by_moves[current_move] = current_index
            current_index = 1
            current_move = nb_move
        else:
            current_index += 1

        puzzle = Puzzle(current_move, grid, int(nb_state), current_index)
        puzzles.append(puzzle)
    max_by_moves[current_move] = current_index

    for puzzle in puzzles:
        puzzle.over = max_by_moves[puzzle.nb_move]

    return puzzles

def get_puzzle(level=None):
    puzzles = load_db('rush.txt')
    if level:
        puzzles = [puzzle for puzzle in puzzles if puzzle.nb_move == level]

    return choice(puzzles)


