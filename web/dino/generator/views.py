import os
import shutil
import threading
from zipfile import ZipFile

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_from_directory,
    redirect,
    abort,
)

from flask_wtf import FlaskForm
from wtforms import RadioField, DecimalField
from wtforms.validators import DataRequired, NumberRange

from dino.generator import cards
from dino.db import get_db


generator = Blueprint("generator", __name__)
running_processes = {}


def _deck_id_from_args(args):
    limits = ""
    for el, (low, high) in args["limits"].items():
        limits += f"-{low},{high}"

    return (
        f"{args['icon']}-{args['nb_move']}-{args['index_move']}-"
        f"{args['n']}-{args['step']}{limits}"
    )


def _get_list_info(deck_id):
    icon, nb_move, index_move, n, step, *limits = deck_id.split("-")
    res = {
        "icon": icon,
        "nb_move": int(nb_move),
        "index_move": int(index_move),
        "n": int(n),
        "step": int(step),
        "url": deck_id + ".zip",
        "deck_id": deck_id,
    }

    for el, limit in zip(["cars", "trucks", "walls"], limits):
        low, high = limit.split(",")
        res[el] = (int(low), int(high))

    return res


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

            card, n_next = cards.generate_front_score_card(
                self.args["icon"], 1, self.args["n"]
            )
            card_filename = "score_front.png"
            card_filepath = os.path.join(cards_dir, card_filename)
            card.save(card_filepath, "PNG")
            card_arcname = os.path.join("recto", f"99.png")
            myzip.write(card_filepath, arcname=card_arcname)

            if n_next != self.args["n"]:
                card = cards.generate_back_score_card(
                    self.args["icon"], n_next, self.args["n"]
                )
            else:
                card = cards.generate_front_title_card(self.args["icon"])
            card_filename = "score_back.png"
            card_filepath = os.path.join(cards_dir, card_filename)
            card.save(card_filepath, "PNG")
            card_arcname = os.path.join("verso", f"99.png")
            myzip.write(card_filepath, arcname=card_arcname)

        shutil.rmtree(cards_dir)
        self.step = "done"


@generator.route("/list")
def list_deck():
    files = [f for f in os.listdir("deck_output") if f.endswith(".zip")]
    return render_template("list.html", files=files)


@generator.route("/api/list")
def api_list_deck():
    files = [
        _get_list_info(os.path.splitext(f)[0])
        for f in os.listdir("deck_output")
        if f.endswith(".zip")
    ]
    return jsonify(files)


@generator.route("/dl/<path:path>")
def dl_deck(path):
    if os.path.isfile(os.path.join("deck_output", path)):
        con = get_db()
        c = con.cursor()
        c.execute("SELECT * FROM dl_count WHERE id = ?", (path,))
        res = c.fetchone()
        if res is None:
            c.execute("INSERT INTO dl_count (id, nb) VALUES (?, ?)", (path, 1))
        else:
            c.execute("UPDATE dl_count SET nb = ? WHERE id = ?", (res["nb"] + 1, path))
        con.commit()
        return send_from_directory(directory="../deck_output", filename=path)

    if os.path.isfile(os.path.join("graphics", "static", "dino", path)):
        return send_from_directory(directory="../graphics/static/dino", filename=path)

    abort(404)


class DeckForm(FlaskForm):
    icon = RadioField(
        "icon",
        choices=[
            ("stegosaurus", "stegosaurus"),
            ("brontosaurus", "brontosaurus"),
            ("elasmosaurus", "elasmosaurus"),
            ("ichthyosaurus", "ichthyosaurus"),
            ("parasaurolophus", "parasaurolophus"),
        ],
        validators=[DataRequired()],
    )
    nb_move = DecimalField(
        "nb_move", validators=[NumberRange(2, 60)], render_kw={"value": 60}
    )
    index_move = DecimalField("index_move", validators=[], render_kw={"value": 1})
    n = DecimalField("n", validators=[NumberRange(1, 84)], render_kw={"value": 84})
    step = DecimalField("step", validators=[], render_kw={"value": 1})
    car_min = DecimalField(
        "car_min", validators=[NumberRange(2, 17)], render_kw={"value": 2}
    )
    car_max = DecimalField(
        "car_max", validators=[NumberRange(2, 17)], render_kw={"value": 17}
    )
    truck_min = DecimalField(
        "truck_min", validators=[NumberRange(0, 10)], render_kw={"value": 0}
    )
    truck_max = DecimalField(
        "truck_max", validators=[NumberRange(0, 10)], render_kw={"value": 4}
    )
    wall_min = DecimalField(
        "wall_min", validators=[NumberRange(0, 2)], render_kw={"value": 0}
    )
    wall_max = DecimalField(
        "wall_max", validators=[NumberRange(0, 2)], render_kw={"value": 0}
    )


@generator.route("/")
@generator.route("/submit_deck", methods=("GET", "POST"))
def submit():
    form = DeckForm(request.form)
    print(form)
    for k in form:
        print(k)
    if form.validate_on_submit():
        print("ok")
        args = {
            "nb_move": form.nb_move.data,
            "index_move": form.index_move.data,
            "icon": form.icon.data,
            "n": form.n.data,
            "step": form.step.data,
            "limits": {
                "cars": (form.car_min.data, form.car_max.data),
                "trucks": (form.truck_min.data, form.truck_max.data),
                "wall": (form.wall_min.data, form.wall_max.data),
            },
        }
        deck_id = _deck_id_from_args(args)
        print(deck_id)
        return redirect("/gen/build/" + deck_id)
    print(form.errors)
    print("nok")
    return render_template("deck_form.html", form=form)


@generator.route("/build/<string:deck_id>")
def build(deck_id):
    return render_template("build.html", deck_id=deck_id)


@generator.route("/api/new_deck/<string:deck_id>")
def build_deck(deck_id):
    # FIXME takes limits from the url
    global running_processes

    args = _get_list_info(deck_id)
    print(args)

    c = get_db().cursor()
    # FIXME query to implement with correct filter
    c.execute("SELECT * FROM games LIMIT :n", {"n": args["n"]})
    # TODO override n with how many row were found

    running_processes[deck_id] = ExportingThread(c.fetchall(), args)
    running_processes[deck_id].start()
    return jsonify({"id": deck_id, "step": "mkcards", "progress": 0})


@generator.route("/api/status/<string:deck_id>")
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


@generator.route("/test")
def test():
    card, n_next = cards.generate_front_score_card("brontosaurus", 1, 84)
    card.save("score_front.png", "PNG")

    card = cards.generate_back_score_card("brontosaurus", n_next, 84)
    card.save("score_back.png", "PNG")
    return "ok"
