import logging
import os

import pyodbc as sql


def validate_depth(depth):
    max_depth = 25
    if not isinstance(depth, int):
        logging.critical(f"Depth '{depth}' is not an integer")
        raise SystemExit
    if depth % 2 != 1:  # only want odd depths, work better with engines
        depth = depth - 1
    if depth > max_depth:
        logging.critical(f"Depth '{depth}' is greater than the max depth of {max_depth}")
        raise SystemExit
    return depth


def validate_file(file):
    if not os.path.isfile(file):
        logging.critical(f"File '{os.path.basename(file)}' does not exist at '{os.path.dirname(file)}'")
        raise SystemExit
    return file


def validate_source(src):
    conn_str = os.getenv('ConnectionStringOdbcRelease')
    qry_text = 'SELECT SourceName FROM ChessWarehouse.dim.Sources'
    source_list = []
    with sql.connect(conn_str) as conn:
        with conn.cursor() as cursor:
            cursor.execute(qry_text)
            source_list = [row[0] for row in cursor.fetchall()]

    if src not in source_list:
        logging.critical(f"Invalid game source '{src}' provided")
        raise SystemExit

    return src


def validate_maxmoves(num):
    if num > 32:
        logging.critical(f"Max move count '{num}' greater than 32")
        raise SystemExit
    return num


def validate_path(path, type):
    if not os.path.isdir(path):
        match type:
            case 'root':
                os.mkdir(os.path.join(path, 'PGN', 'Archive'))
                os.mkdir(os.path.join(path, 'Output', 'Archive'))
            case 'engine':
                logging.critical(f"Engine directory '{path}' does not exist")
                raise SystemExit
            case _:
                logging.critical(f'Unknown directory type {type} passed')
                raise SystemExit

    return path
