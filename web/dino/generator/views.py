from dino.db import get_db
import sqlite3
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
    jsonify,
    send_from_directory,
)

import random
import threading
import time


generator = Blueprint("generator", __name__)
exporting_threads = {}


class ExportingThread(threading.Thread):
    def __init__(self, rows, args):
        super().__init__()
        self.rows = rows
        self.args = args
        self.progress = 0

    def run(self):
        # shutil.rmtree('generated', ignore_errors=True)
        # os.makedirs('generated')

        # generate_title_card(icon, deck_parameter_str)
        res = ""
        parity = True
        for i, row in enumerate(self.rows):
            res += str(tuple(row)) + "<br>"

            card = generate_card(
                row, deck=self.args["icon"], current_pos=(i, self.args["n"])
            )

            time.sleep(1)
            self.progress = 100 * i // (self.args["n"] - 1)
            print(self.progress)

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


@generator.route("api/new_deck")
def build_deck():
    # FIXME takes limits from the url
    global exporting_threads

    thread_id = random.randint(0, 10000)
    c = get_db().cursor()
    # FIXME query to implement with correct filter
    c.execute("SELECT * FROM games LIMIT :n", {"n": 15})

    exporting_threads[thread_id] = ExportingThread(
        c.fetchall(),
        {
            "nb_move": 50,
            "index_move": 1,
            "icon": None,
            "n": 15,
            "limits": None,
            "step": 1,
        },
    )
    exporting_threads[thread_id].start()
    return jsonify({"id": thread_id, "progress": 0})


@generator.route("/")
def test():
    return send_from_directory("templates", "build.html")


@generator.route("api/status/<int:deck_id>")
def progress(deck_id):
    global exporting_threads
    print(deck_id)
    return jsonify({"id": deck_id, "progress": exporting_threads[deck_id].progress})


def generate_card(row, deck, current_pos):
    return None
