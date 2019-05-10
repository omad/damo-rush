from flaskr.db import get_db
from flask import Blueprint, flash, redirect, render_template, request, url_for

generator = Blueprint("generator", __name__)


@generator.route("/build")
def build_deck():
    # FIXME takes limits from the url
    return generate_deck()


def generate_card(row, deck, current_pos):
    return None


def generate_deck(nb_move=60, index_move=1, icon=None, n=15, limits=None, step=1):
    assert nb_move <= 60
    # shutil.rmtree('generated', ignore_errors=True)
    # os.makedirs('generated')

    deck_parameter_str = f"({nb_move},{index_move}),{n}:{step},{limits}".replace(
        " ", ""
    )
    # generate_title_card(icon, deck_parameter_str)

    db = get_db()
    c = db.cursor()
    res = ""
    parity = True
    # FIXME query to implement with correct filter
    for i, row in enumerate(c.execute("SELECT * FROM games LIMIT :n", {"n": n})):
        res += str(tuple(row)) + "<br>"

        card = generate_card(row, deck=icon, current_pos=(i, n))
        """
        parity = 'odd' if n % 2 else 'even'
        card.save(
            os.path.join('generated',
            f"{icon}-{['odd', 'even']parity}-{n + 1:0{len_n}d}.png"),
            'PNG'
        )
        parity ^= True
        print(f'[Card] {icon} {n + 1} generated ({puzzle.nb_move}, {puzzle.index}/{puzzle.over})')
        """

    return res
