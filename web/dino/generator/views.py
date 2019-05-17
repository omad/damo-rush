import os
import shutil
import threading
from zipfile import ZipFile

from flask import Blueprint, render_template, request, jsonify, send_from_directory

from dino.generator import cards
from dino.db import get_db


generator = Blueprint("generator", __name__)
running_processes = {}


def deck_id_from_args(args):
    return (
        f"{args['icon']}-{args['nb_move']}-{args['index_move']}-"
        f"{args['n']}-{args['step']}-{args['limits']}"
    )


class ExportingThread(threading.Thread):
    def __init__(self, rows, args):
        super().__init__()
        self.rows = rows
        self.args = args
        self.progress = 0
        self.step = None

    def run(self):
        if not os.path.exists("deck_output"):
            os.makedirs("deck_output")

        deck_path = os.path.join("deck_output", f"{self.args['deck_id']}.zip")
        if os.path.exists(deck_path):
            self.progress = 100
            self.step = "done"
            return

        # TODO delete oldest zip if total space taken too high

        # TODO generate_title_card(icon, deck_parameter_str)
        self.step = "mkcards"

        cards_dir = os.path.join("deck_output", str(self.args["deck_id"]))

        if not os.path.exists(cards_dir):
            os.makedirs(cards_dir)

        with ZipFile(deck_path, "w") as myzip:
            # front title card
            card = cards.generate_front_title_card(self.args["icon"])
            card_filename = "front.png"
            card_filepath = os.path.join(cards_dir, card_filename)
            card_arcname = os.path.join(
                "recto", f"{0:0{len(str(1 + self.args['n'] // 2))}d}.png"
            )
            card.save(card_filepath, "PNG")
            myzip.write(card_filepath, arcname=card_arcname)
            self.progress = 100 * 1 // (self.args["n"] + 2)

            # back title card
            card = cards.generate_back_title_card()
            card_filename = "back.png"
            card_filepath = os.path.join(cards_dir, card_filename)
            card_arcname = os.path.join(
                "verso", f"{0:0{len(str(1 + self.args['n'] // 2))}d}.png"
            )
            card.save(card_filepath, "PNG")
            myzip.write(card_filepath, arcname=card_arcname)
            self.progress = 100 * 2 // (self.args["n"] + 2)

            for i, row in enumerate(self.rows):
                side = "verso" if i % 2 else "recto"
                card_filename = f"{i + 1}.png"
                card_arcname = os.path.join(
                    side, f"{1 + i // 2:0{len(str(1 + self.args['n'] // 2))}d}.png"
                )

                card_filepath = os.path.join(cards_dir, card_filename)
                deck_info = {
                    "icon": self.args["icon"],
                    "text": f"{i+1:0{len(str(self.args['n']))}d}",
                }

                card = cards.generate_puzzle_card(row, deck_info)
                card.save(card_filepath, "PNG")
                myzip.write(card_filepath, arcname=card_arcname)

                print(
                    f"[Card] {self.args['icon']} {i + 1} generated "
                    f"({row['nb_move']}, {row['index_']}/{row['index_max']})"
                )
                self.progress = 100 * (i + 3) // (self.args["n"] + 2)
        shutil.rmtree(cards_dir)
        self.step = "done"


@generator.route("/")
def test():
    return render_template("build.html")


@generator.route("api/new_deck")
def build_deck():
    # FIXME takes limits from the url
    global running_processes

    args = {
        "nb_move": 50,
        "index_move": 1,
        "icon": "brontosaurus",
        "n": 50,
        "limits": None,
        "step": 1,
    }
    deck_id = deck_id_from_args(args)
    args["deck_id"] = deck_id

    c = get_db().cursor()
    # FIXME query to implement with correct filter
    c.execute("SELECT * FROM games LIMIT :n", {"n": args["n"]})
    # TODO override n with how many row were found

    running_processes[deck_id] = ExportingThread(c.fetchall(), args)
    running_processes[deck_id].start()
    return jsonify({"id": deck_id, "step": "mkcards", "progress": 0})


@generator.route("api/status/<string:deck_id>")
def progress(deck_id):
    global running_processes
    if deck_id not in running_processes:
        # check if present in file
        return jsonify(
            {
                "id": deck_id,
                "step": "missing",
                "progress": running_processes[deck_id].progress,
            }
        )

    return jsonify(
        {
            "id": deck_id,
            "step": running_processes[deck_id].step,
            "progress": running_processes[deck_id].progress,
        }
    )
