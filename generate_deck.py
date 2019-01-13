#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
from mkcard import make_card, make_front_title_card, make_back_title_card
from mkcard import NotPlayableWithRegularGame

from common import load_db


def generate_title_card(icon):
    front = make_front_title_card(icon)
    front.save(os.path.join('generated', f'{icon}-front.png'), 'PNG')
    print(f'[Card] {icon} front generated')
    back = make_back_title_card(icon)
    back.save(os.path.join('generated', f'{icon}-back.png'), 'PNG')
    print(f'[Card] {icon} back generated')


def generate_deck(nb_move, index_move, icon, n):
    assert nb_move <= 60
    shutil.rmtree('generated', ignore_errors=True)
    os.makedirs('generated')

    generate_title_card(icon)

    puzzles = load_db('rush.txt')

    i = [puzzle.nb_move for puzzle in puzzles].index(nb_move) + index_move - 1

    len_n = len(str(n))
    while n:
        if i < len(puzzles):
            puzzle = puzzles[i]
        else:
            raise IndexError('Not enough grid corresponding to the constraint in the database')

        try:
            card = make_card(puzzle, deck=icon, n=n, len_n=len_n)
            n -= 1
        except NotPlayableWithRegularGame:
            print(f'[Card] {puzzle.grid} is not playable with a regular game, skipping it...')
            i += 1
            continue

        parity = 'odd' if n % 2 else 'even'
        card.save(os.path.join('generated', f'{icon}-{parity}-{n + 1:0{len_n}d}.png'), 'PNG')
        print(f'[Card] {icon} {n + 1} generated ({puzzle.nb_move}, {puzzle.index}/{puzzle.over})')

        i += 1

    print(f'[Info] use {puzzles[i].nb_move, puzzles[i].index} to generate the continuing deck')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a deck of card')
    parser.add_argument('level', type=int)
    parser.add_argument('index', type=int)
    parser.add_argument('icon', type=str)
    parser.add_argument('n', type=int, default=6, nargs='?')
    args = parser.parse_args()
    generate_deck(args.level, args.index, args.icon, args.n)
