from collections import Counter, defaultdict
import sqlite3
import json
import os


def get_elements(grid):
    elements = defaultdict(list)
    nb_wall = 0
    for i, c in enumerate(grid):
        if c != "o":
            if c == "x":
                nb_wall += 1
                c = "x" + str(nb_wall)
            elements[c].append(i)
    return elements


def create_db(grid_txt_file, db_file):
    if os.path.exists(db_file):
        return
        # os.remove(db_file) # used for debug

    print(f"[DB] Creating database {db_file} from grid file {grid_txt_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE games (
          [id] INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
          [nb_move] integer,
          [index_] integer,
          [index_max] integer,
          [nb_state] integer,
          [elements] text,
          [nb_wall] integer,
          [nb_car] integer,
          [nb_truck] integer
        )"""
    )
    conn.commit()

    current_move = 0
    current_index = 0
    batch_to_ingest = []
    last_count = 0

    lines = open(grid_txt_file, "r").readlines()
    # Dummy stop line to trigger last ingest
    lines.append("999 aaoooooooooooooooooooooooooooooooooo 0")
    lines = lines[::-1]
    # lines = lines[:1000] + lines[-1000:]  # quicker tests

    while lines:
        line = lines.pop()
        nb_move, grid, nb_state = line.split()
        nb_move = int(nb_move)
        if nb_move != current_move:
            for puzzle in batch_to_ingest:
                puzzle["index_max"] = current_index - 1

            if batch_to_ingest:
                cursor.executemany(
                    """
                    INSERT INTO games (
                      nb_move,
                      index_,
                      index_max,
                      nb_state,
                      elements,
                      nb_wall,
                      nb_car,
                      nb_truck
                    ) VALUES (
                      :nb_move,
                      :index,
                      :index_max,
                      :nb_state,
                      :elements,
                      :nb_wall,
                      :nb_car,
                      :nb_truck
                    )
                    """,
                    batch_to_ingest,
                )
                print(
                    f"{conn.total_changes - last_count:>7,} row(s) ingested "
                    f"for nb_move = {current_move}"
                )
                last_count = conn.total_changes

            batch_to_ingest = []
            current_move = nb_move
            current_index = 0

        current_index += 1
        elements = get_elements(grid)
        nb_elements = Counter(len(v) for v in elements.values())
        puzzle = {
            "nb_move": nb_move,
            "index": current_index,
            "index_max": 0,
            "nb_state": int(nb_state),
            "elements": json.dumps(elements),
            "nb_wall": nb_elements[1],
            "nb_car": nb_elements[2],
            "nb_truck": nb_elements[3],
        }
        batch_to_ingest.append(puzzle)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db("../cli/rush.txt", "rush.db")
