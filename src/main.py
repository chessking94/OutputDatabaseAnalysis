import csv
import datetime as dt
import logging
import os

import chess
import chess.engine
import chess.pgn
import pandas as pd
import pyodbc as sql

from api import bookmoves, tbsearch
import format
from func import tbeval, piececount, get_conf, get_config, get_parentdirs
import validate as v

DELIM = '\t'


def main():
    logging.basicConfig(format='%(asctime)s\t%(funcName)s\t%(levelname)s\t%(message)s', level=logging.INFO)
    logging.info('START PROCESSING')

    config_path = get_parentdirs(os.path.dirname(__file__), 1)

    # parameters
    root_path = v.validate_path(get_config(config_path, 'rootPath'), 'root')
    pgn_path = os.path.join(root_path, 'PGN')
    output_path = os.path.join(root_path, 'Output')
    engine_path = v.validate_path(get_config(config_path, 'enginePath'), 'engine')
    pgn_name = v.validate_file(pgn_path, get_config(config_path, 'pgnName'))
    source_name = v.validate_source(get_config(config_path, 'sourceName'))

    source_params = get_config(config_path, 'sourceParameters')[source_name]
    d = v.validate_depth(source_params['depth'])
    engine_name = source_params['engineName']
    seed_gameid = source_params['seedGameID']
    openings = source_params['useOpeningExplorer']
    tblbase = source_params['useTablebaseExplorer']
    max_moves = v.validate_maxmoves(source_params['maxMoves'])
    tmctrl_default = get_config(config_path, 'timeControlDetailDefault')

    # initiate engine
    eng = os.path.splitext(engine_name)[0]
    engine = chess.engine.SimpleEngine.popen_uci(os.path.join(engine_path, engine_name))

    # get next game id value
    if seed_gameid:
        conn_str = get_conf('SqlServerConnectionStringTrusted')
        conn = sql.connect(conn_str)
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
    with open(full_pgn, mode='r', encoding='utf-8') as pgn:
        ctr = 1
        game_text = chess.pgn.read_game(pgn)
        while game_text is not None:
            board = chess.Board(chess.STARTING_FEN)
            eventname = format.get_tag(game_text, 'Event')
            whitelast, whitefirst = format.get_name(game_text, 'White')
            blacklast, blackfirst = format.get_name(game_text, 'Black')
            whiteelo = format.get_tag(game_text, 'WhiteElo')
            blackelo = format.get_tag(game_text, 'BlackElo')
            roundnum = format.get_tag(game_text, 'Round')
            eco = format.get_tag(game_text, 'ECO')
            gamedate, date_val = format.get_date(game_text, 'Date')
            gametime = format.get_tag(game_text, 'UTCTime')
            result = format.get_result(game_text, 'Result')
            site, gameid = format.get_sourceid(game_text, 'Site')
            if not gameid:
                gameid = seed
            tmctrl = format.get_tag(game_text, 'TimeControl')
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

                istheory = 1 if openings else 0
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
                        if board.san(mv) not in bookmoves(fen, date_val):
                            istheory = 0
                    istablebase = 0
                    if tblbase:
                        istablebase = 1 if piececount(fen) <= 7 else istablebase
                    clk = int(node.clock()) if node.clock() is not None else ''
                    if color == 'White':
                        ts = format.calc_timespent(white_prevtime, node.clock(), incr)
                        white_prevtime = node.clock()
                    else:
                        ts = format.calc_timespent(black_prevtime, node.clock(), incr)
                        black_prevtime = node.clock()
                    phaseid = format.calc_phase(fen, phaseid)

                    move_dict = {'T' + str(ii + 1):  '' for ii in range(max_moves)}
                    eval_dict = {'T' + str(ii + 1) + '_Eval':  '' for ii in range(max_moves)}

                    if not istablebase:
                        dp = d
                        info = engine.analyse(board, limit=chess.engine.Limit(depth=d), multipv=max_moves, options={'Threads': 8})
                        i = 1
                        for line in info:
                            tmp_move = board.san(line['pv'][0])
                            tmp_eval = format.format_eval(str(line['score'].white()))
                            move_dict.update({'T' + str(i): tmp_move})
                            eval_dict.update({'T' + str(i) + '_Eval': tmp_eval})
                            i = i + 1

                        if move not in move_dict.values():
                            info = engine.analyse(board, chess.engine.Limit(depth=d), root_moves=[mv], options={'Threads': 8})
                            move_eval = format.format_eval(str(info['score'].white()))
                            move_rank = max_moves + 1
                        else:
                            key = [k for k, v in move_dict.items() if v == move]
                            move_eval = eval_dict[f'{key[0]}_Eval']
                            evm_list = [int(k[1:3].strip('_')) for k, v in eval_dict.items() if v == move_eval]
                            move_rank = min(evm_list)
                    else:
                        tbresults = tbsearch(fen)
                        k = 0
                        for entry in tbresults:
                            if entry[0] == board.san(mv):
                                move_rank = k
                                break
                            k = k + 1

                        move_eval = tbeval(tbresults[move_rank])
                        dp = 0

                        mv_iter = min(max_moves, len(tbresults))
                        for i in range(mv_iter):
                            tmp_move = str(tbresults[i][0])
                            tmp_eval = tbeval(tbresults[i])
                            move_dict.update({'T' + str(i + 1): tmp_move})
                            eval_dict.update({'T' + str(i + 1) + '_Eval': tmp_eval})

                        evm_list = [int(k[1:3].strip('_')) for k, v in eval_dict.items() if v == move_eval]
                        move_rank = min(evm_list)

                    t1_eval = eval_dict['T1_Eval']
                    if str(t1_eval).startswith('#') or str(move_eval).startswith('#') or istablebase:
                        cp_loss = ''
                    else:
                        cp_loss = '{:3.2f}'.format(abs(t1_eval - move_eval))

                    move_rec = [
                        'M', gameid, movenum, color, istheory, istablebase, eng, dp, clk, ts, fen, phaseid,
                        move, move_eval, move_rank, cp_loss
                    ]
                    for i in range(max_moves):
                        move_rec.append(move_dict[f'T{i + 1}'])
                        move_rec.append(eval_dict[f'T{i + 1}_Eval'])

                    while len(move_rec) <= 79:
                        move_rec.append('')

                    # MOVE RECORD
                    with open(full_output, 'a', newline='') as f:
                        writer = csv.writer(f, delimiter=DELIM)
                        writer.writerow(move_rec)

                    board.push(mv)

                logging.info(f'Completed processing game {ctr}')
                seed = seed + 1

            game_text = chess.pgn.read_game(pgn)
            ctr = ctr + 1

    engine.quit()
    logging.info('END PROCESSING')


if __name__ == '__main__':
    main()
