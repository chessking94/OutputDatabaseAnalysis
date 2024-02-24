import csv
import datetime as dt
import logging
import os

from automation import misc
import chess
import chess.engine
import chess.pgn
import pandas as pd
import sqlalchemy as sa

from api import bookmoves, tbsearch
from constants import CONFIG_FILE, DELIM
import format
from func import tbeval, piececount
import validate as v

# TODO: Investigate the possibility of a move depth record; i.e. one that lists the top move/eval at a given depth
# TODO: New game source for Chess.com and/or accounts closed as cheating


def main():
    logging.basicConfig(format='%(asctime)s\t%(funcName)s\t%(levelname)s\t%(message)s', level=logging.INFO)
    logging.info('START PROCESSING')

    # parameters
    root_path = v.validate_path(misc.get_config('rootPath', CONFIG_FILE), 'root')
    pgn_path = os.path.join(root_path, 'PGN')
    output_path = os.path.join(root_path, 'Output')
    engine_path = v.validate_path(misc.get_config('enginePath', CONFIG_FILE), 'engine')
    pgn_name = v.validate_file(pgn_path, misc.get_config('pgnName', CONFIG_FILE))
    source_name = v.validate_source(misc.get_config('sourceName', CONFIG_FILE))

    source_params = misc.get_config('sourceParameters', CONFIG_FILE)[source_name]
    d = v.validate_depth(source_params['depth'])
    engine_name = source_params['engineName']
    seed_gameid = source_params['seedGameID']
    openings = source_params['useOpeningExplorer']
    tblbase = source_params['useTablebaseExplorer']
    max_moves = v.validate_maxmoves(source_params['maxMoves'])
    tmctrl_default = misc.get_config('timeControlDetailDefault', CONFIG_FILE)
    istheorydefault = misc.get_config('isTheoryDefault', CONFIG_FILE)

    # initiate engine
    eng = os.path.splitext(engine_name)[0]
    engine = chess.engine.SimpleEngine.popen_uci(os.path.join(engine_path, engine_name))

    # get next game id value
    if seed_gameid:
        conn_str = misc.get_config('connectionString_chessDB', CONFIG_FILE)
        connection_url = sa.engine.URL.create(
            drivername='mssql+pyodbc',
            query={"odbc_connect": conn_str}
        )
        engine = sa.create_engine(connection_url)
        conn = engine.connect().connection
        qry_text = f"""
SELECT
ISNULL(MAX(CAST(g.SiteGameID AS int)), 0) + 1

FROM ChessWarehouse.lake.Games g
JOIN ChessWarehouse.dim.Sources src ON g.SourceID = src.SourceID

WHERE src.SourceName = '{source_name}'
"""
        seed = int(pd.read_sql(qry_text, conn).values[0][0])
        conn.close()
    else:
        seed = 1

    # input/output stuff
    dte = dt.datetime.now().strftime('%Y%m%d%H%M%S')
    output_file = f'{os.path.splitext(pgn_name)[0]}_{dte}.game'
    full_pgn = os.path.join(pgn_path, pgn_name)
    full_output = os.path.join(output_path, output_file)
    with open(full_pgn, mode='r', encoding='utf-8') as gmct:
        tot_gms = 0
        search_text = '[Event "'
        for line in gmct:
            if search_text in line:
                tot_gms = tot_gms + 1
    with open(full_pgn, mode='r', encoding='utf-8') as pgn:
        ctr = 1
        game_text = chess.pgn.read_game(pgn)
        while game_text is not None:
            board = chess.Board(chess.STARTING_FEN)
            eventname = format.get_tag(game_text.headers.get('Event'))
            whitelast, whitefirst = format.get_name(game_text.headers.get('White'))
            blacklast, blackfirst = format.get_name(game_text.headers.get('Black'))
            whiteelo = format.get_tag(game_text.headers.get('WhiteElo'))
            blackelo = format.get_tag(game_text.headers.get('BlackElo'))
            roundnum = format.get_tag(game_text.headers.get('Round'))
            eco = format.get_tag(game_text.headers.get('ECO'))
            dt_tag = 'Date' if game_text.headers.get('Date') is not None else 'UTCDate'  # old Lichess games are missing the Date tag, use UTCDate instead
            gamedate, date_val = format.get_date(game_text.headers.get(dt_tag))
            gametime = format.get_tag(game_text.headers.get('UTCTime'))
            result = format.get_result(game_text.headers.get('Result'))
            site, gameid = format.get_sourceid(game_text.headers.get('Site'), game_text.headers.get('Link'), game_text.headers.get('FICSGamesDBGameNo'))
            if not gameid:
                gameid = seed
            tmctrl = format.get_tag(game_text.headers.get('TimeControl'))
            if not tmctrl:
                tmctrl = tmctrl_default
            incr = tmctrl[tmctrl.index('+')+1:len(tmctrl)].strip() if '+' in tmctrl else '0'
            game_rec = [
                'G', source_name, site, gameid,
                whitelast, whitefirst, blacklast, blackfirst, whiteelo, blackelo,
                tmctrl, eco, gamedate, gametime, eventname, roundnum, result
            ]
            while len(game_rec) <= 79:
                game_rec.append('')

            if whitelast == '' or blacklast == '':
                logging.error(f'PGN game {ctr} was missing names and not processed!')
            else:
                # GAME RECORD
                with open(full_output, 'a', newline='') as f:
                    writer = csv.writer(f, delimiter=DELIM)
                    writer.writerow(game_rec)

                istheory = 1
                phaseid = 1
                white_prevtime = None
                black_prevtime = None

                for node in game_text.mainline():
                    mv = node.move
                    move = board.san(mv)
                    fen = board.fen()
                    movenum = board.fullmove_number
                    color = 'White' if board.turn else 'Black'

                    logging.debug(f'{ctr} {seed} {color} {movenum}')

                    if istheory == 1:
                        if openings:
                            if board.san(mv) not in bookmoves(fen, date_val):
                                istheory = 0
                        else:
                            if movenum > istheorydefault:
                                istheory = 0
                    istablebase = 1 if piececount(fen) <= 7 else 0
                    clk = int(node.clock()) if node.clock() is not None else ''
                    if color == 'White':
                        ts = format.calc_timespent(white_prevtime, node.clock(), incr)
                        white_prevtime = node.clock()
                    else:
                        ts = format.calc_timespent(black_prevtime, node.clock(), incr)
                        black_prevtime = node.clock()
                    phaseid = format.calc_phase(fen, phaseid)

                    move_arr = ['' for ii in range(max_moves)]
                    eval_arr = ['' for ii in range(max_moves)]

                    if not istablebase or not tblbase:
                        dp = d
                        info = engine.analyse(board, limit=chess.engine.Limit(depth=d), multipv=max_moves, options={'Threads': 8})
                        i = 0
                        for line in info:
                            tmp_move = board.san(line['pv'][0])
                            tmp_eval = format.format_eval(str(line['score'].white()))
                            move_arr[i] = tmp_move
                            eval_arr[i] = line['score'].white()
                            i = i + 1

                        if move not in move_arr:
                            info = engine.analyse(board, chess.engine.Limit(depth=d), root_moves=[mv], options={'Threads': 8})
                            move_eval = info['score'].white()

                            for ix, x in enumerate(eval_arr):
                                if color == 'White':
                                    a, b = move_eval, x
                                else:
                                    a, b = x, move_eval
                                if a >= b:
                                    move_arr.insert(ix, move)
                                    eval_arr.insert(ix, move_eval)
                                    break
                        if move in move_arr:
                            idx = move_arr.index(move)
                            move_eval = format.format_eval(str(eval_arr[idx]))
                        else:
                            move_eval = format.format_eval(str(move_eval))
                        eval_arr = [format.format_eval(str(ev)) for ev in eval_arr]
                    else:
                        tbresults = tbsearch(fen)
                        k = 0
                        for entry in tbresults:
                            if entry[0] == board.san(mv):
                                move_idx = k
                                break
                            k = k + 1

                        move_eval = tbeval(tbresults[move_idx])
                        dp = 0

                        mv_iter = min(max_moves, len(tbresults))
                        for i in range(mv_iter):
                            tmp_move = str(tbresults[i][0])
                            tmp_eval = tbeval(tbresults[i])
                            move_arr[i] = tmp_move
                            eval_arr[i] = tmp_eval

                    if move_eval in eval_arr:
                        move_rank = eval_arr.index(move_eval) + 1
                    else:
                        move_rank = max_moves + 1

                    t1_eval = eval_arr[0]
                    if str(t1_eval).startswith('#') or str(move_eval).startswith('#') or istablebase:
                        cp_loss = ''
                    else:
                        cp_loss = '{:3.2f}'.format(abs(t1_eval - move_eval))

                    move_rec = [
                        'M', gameid, movenum, color, istheory, istablebase, eng, dp, clk, ts, fen, phaseid,
                        move, move_eval, move_rank, cp_loss
                    ]
                    for i in range(max_moves):
                        move_rec.append(move_arr[i])
                        move_rec.append(eval_arr[i])

                    while len(move_rec) <= 79:
                        move_rec.append('')

                    # MOVE RECORD
                    with open(full_output, 'a', newline='') as f:
                        writer = csv.writer(f, delimiter=DELIM)
                        writer.writerow(move_rec)

                    board.push(mv)

                logging.info(f'Completed processing game {ctr} of {tot_gms}')
                seed = seed + 1

            game_text = chess.pgn.read_game(pgn)
            ctr = ctr + 1

    engine.quit()
    logging.info('END PROCESSING')


if __name__ == '__main__':
    main()
