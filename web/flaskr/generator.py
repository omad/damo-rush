from flaskr.db import get_db


def generate_deck(nb_move=60, index_move=1, icon=None, n=10, limits=None, step=1):
    assert nb_move <= 60
    #shutil.rmtree('generated', ignore_errors=True)
    #os.makedirs('generated')

    deck_parameter_str = f'({nb_move},{index_move}),{n}:{step},{limits}'.replace(' ', '')
    #generate_title_card(icon, deck_parameter_str)

    db = get_db()
    c = db.cursor()
    for row in c.execute('SELECT * FROM games LIMIT ?', n):
        print(row)

    """
    puzzles = load_db('rush.txt')

    i = [puzzle.nb_move for puzzle in puzzles].index(nb_move) + index_move - 1

    len_n = len(str(n))
    while n:
        if i < len(puzzles):
            puzzle = puzzles[i]
        else:
            raise IndexError('Not enough grid corresponding to the constraint in the database')

        try:
            card = make_card(puzzle, deck=icon, n=n, len_n=len_n, limits=limits)
            n -= 1
        except NotPlayableWithRegularGame:
            i += 1
            continue

        parity = 'odd' if n % 2 else 'even'
        card.save(os.path.join('generated', f'{icon}-{parity}-{n + 1:0{len_n}d}.png'), 'PNG')
        print(f'[Card] {icon} {n + 1} generated ({puzzle.nb_move}, {puzzle.index}/{puzzle.over})')

        i += step

    print(f'[Info] use level, index = {puzzles[i].nb_move, puzzles[i].index} to generate the continuing deck')
    """
