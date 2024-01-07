import logging
import os

from . import CONFIG_FILE
from automation import misc
import pandas as pd
import pyodbc as sql


def validate_depth(depth):
    max_depth = 25
    if not isinstance(depth, int):
        logging.critical(f'Depth {depth} is not an integer')
        raise SystemExit
    if depth % 2 != 1:  # only want odd depths, work better with engines
        depth = depth - 1
    if depth > max_depth:
        logging.critical(f'Depth {depth} is greater than the max depth of {max_depth}')
        raise SystemExit
    return depth


def validate_file(path, file):
    if not os.path.isfile(os.path.join(path, file)):
        logging.critical(f'File {file} does not exist at {path}')
        raise SystemExit
    return file


def validate_source(src):
    conn_str = misc.get_config('connectionString_chessDB', CONFIG_FILE)
    conn = sql.connect(conn_str)
    qry_text = 'SELECT SourceName FROM ChessWarehouse.dim.Sources'
    source_list = pd.read_sql(qry_text, conn).stack().tolist()
    conn.close()
    if src not in source_list:
        logging.critical(f'Invalid game source {src} provided')
        raise SystemExit
    return src


def validate_maxmoves(num):
    if num > 32:
        logging.critical(f'Max move count {num} greater than 32')
        raise SystemExit
    return num


def validate_path(path, type):
    if not os.path.isdir(path):
        if type == 'root':
            logging.info(f'Created new analysis directory {path}')
            os.mkdir(os.path.join(path, 'PGN', 'Archive'))
            os.mkdir(os.path.join(path, 'Output', 'Archive'))
        elif type == 'engine':
            logging.critical(f'Engine directory {path} does not exist')
            raise SystemExit
        else:
            logging.critical(f'Unknown directory type {type} passed')
            raise SystemExit
    return path
