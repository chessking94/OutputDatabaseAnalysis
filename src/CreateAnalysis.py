import datetime as dt
import logging
import os
import time

import chess
import chess.engine
import chess.pgn
import pandas as pd
import pyodbc as sql

from api import bookmoves, tbsearch
from conf import get_connstr
import format
from func import tbeval, piececount


def main():
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    # parameters
    pgn_path = r'C:\Users\eehunt\Documents\Chess\Analysis\PGN'
    output_path = r'C:\Users\eehunt\Documents\Chess\Analysis\Output'
    engine_path = r'C:\Users\eehunt\Documents\Chess\ENGINES'

    d = 11
    corrflag = '0' # careful!
    db = 1
    pgn_name = 'EEH_Online_All_202207.pgn'
    engine_name = 'stockfish_11_x64.exe'
    row_delim = '\n'

    game_type = 'Test'
    if game_type == 'EEH':
        d = 15
        db_name = 'EEHGames'
    elif game_type == 'Online':
        db_name = 'OnlineGames'
        engine_name = 'stockfish_14.1_x64.exe'
    elif game_type == 'Control':
        db_name = 'ControlGames'
    elif game_type == 'Test':
        db = 0
    else:
        logging.critical('Invalid game type!')
        quit()

    # initiate engine
    eng = os.path.splitext(engine_name)[0].ljust(25, ' ')
    engine = chess.engine.SimpleEngine.popen_uci(os.path.join(engine_path, engine_name))

    # get game id value
    if db == 1:
        conn_str = get_connstr()
        conn = sql.connect(conn_str)
        qry_text = f"SELECT IDENT_CURRENT('{db_name}') + 1 AS GameID"
        qry_rec = pd.read_sql(qry_text, conn).values.tolist()
        gameid = int(qry_rec[0][0])
        conn.close()
    else:
        gameid = 1

    # input/output stuff
    dte = dt.datetime.now().strftime('%Y%m%d%H%M%S')
    output_file = f'{os.path.splitext(pgn_name)[0]}_Processed_{dte}.txt'
    full_pgn = os.path.join(pgn_path, pgn_name)
    full_output = os.path.join(output_path, output_file)
    pgn = open(full_pgn, 'r')

    logging.info(f"BEGIN PROCESSING: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    ctr = 1
    game_text = chess.pgn.read_game(pgn)
    while game_text is not None:
        board = chess.Board(chess.STARTING_FEN)
        tournament = format.tournament(game_text, 'Event')
        whitelast, whitefirst = format.name(game_text, 'White')
        blacklast, blackfirst = format.name(game_text, 'Black')
        whiteelo = format.elo(game_text, 'WhiteElo')
        blackelo = format.elo(game_text, 'BlackElo')
        roundnum = format.round(game_text, 'Round')
        eco = format.eco(game_text, 'ECO')
        gamedate, date_val = format.date(game_text, 'Date')
        result = format.result(game_text, 'Result')
        moves = format.moves(game_text, 'PlyCount')
        src, srcid = format.source_id(game_text, 'Site')
        tmctrl = format.timecontrol(game_text, 'TimeControl')
        
        if whitelast == '' or blacklast == '':
            logging.error(f'PGN game {ctr} was missing names and not processed!')
        else:
            # RECORD 01: PRIMARY GAME INFORMATION
            with open(full_output, 'a') as f:
                f.write('01' + whitelast + whitefirst + whiteelo + blacklast + 
                        blackfirst + blackelo + eco + gamedate + tournament +
                        roundnum + result + moves + corrflag + src + srcid + tmctrl + row_delim)

            istheory = '1'
            for node in game_text.mainline():
                mv = node.move
                s_time = time.time()
                fen = board.fen()
                clk = str(int(node.clock())).ljust(7, ' ') if node.clock() is not None else ''.ljust(7, ' ')
                ev = node.eval().white() if node.eval() is not None else None
                pgn_eval = format.pgneval(ev).ljust(6, ' ')
                
                if istheory == '1':
                    if board.san(mv) not in bookmoves(fen, date_val):
                        istheory = '0'
                
                if piececount(fen) > 7:
                    istablebase = '0'
                    if board.turn:
                        color = 'White'
                    else:
                        color = 'Black'
                    
                    eval_properA = []
                    eval_list = []
                    move_list = []
                    logging.info(f'{ctr} {gameid} {color} {board.fullmove_number}')
                    
                    for lgl in board.legal_moves:
                        info = engine.analyse(board, chess.engine.Limit(depth=d), root_moves=[lgl], options={'Threads': 8})
                        evals = str(info['score'].white())
                        move_list.append(board.san(lgl))

                        if evals.startswith('#'):
                            eval_p = int(evals[1:len(evals)])
                            eval_properA.append(chess.engine.Mate(eval_p))
                            eval_list.append(evals)
                        else:
                            eval_p = float(evals)
                            eval_properA.append(chess.engine.Cp(eval_p))
                            evals = round(int(evals)/100., 2)
                            eval_list.append(evals)

                    move_sort = [x for _, x in sorted(zip(eval_properA, move_list), reverse=board.turn)]
                    eval_sort = [y for _, y in sorted(zip(eval_properA, eval_list), reverse=board.turn)]
                            
                    if board.san(mv) not in move_sort[0:31]:
                        info = engine.analyse(board, chess.engine.Limit(depth=d), root_moves=[mv], options={'Threads': 8})
                        move = board.san(mv)
                        move_eval = str(info['score'].white())
                        if not board.turn:
                            if move_eval.find('-') >= 0:
                                move_eval = move_eval.replace('-', '+')
                            else:
                                move_eval = move_eval.replace('+', '-')
                        if not move_eval.startswith('#'):
                            move_eval = round(int(move_eval)/100., 2)
                    else:
                        move = board.san(mv)
                        i = move_sort[0:31].index(move)
                        move_eval = eval_sort[i]
                    
                    e_time = str(round(time.time() - s_time, 4)).ljust(8, ' ')
                    movenum = str(board.fullmove_number).ljust(3, ' ')

                    # create dictionaries of moves and evals
                    move_dict = {'T' + str(ii + 1):  ''.ljust(7, ' ') for ii in range(32)}
                    eval_dict = {'T' + str(ii + 1) + '_Eval':  ''.ljust(6, ' ') for ii in range(32)}

                    mv_iter = 32 if len(move_sort) >= 32 else len(move_sort)
                    for i in range(mv_iter):
                        tmp_move = str(move_sort[i]).ljust(7, ' ')
                        tmp_eval = str(eval_sort[i]).ljust(6, ' ')
                        move_dict.update({'T' + str(i + 1): tmp_move})
                        eval_dict.update({'T' + str(i + 1) + '_Eval': tmp_eval})
                    
                    mv_conc = ''
                    for mv_val in move_dict:
                        mv_conc = mv_conc + move_dict[mv_val]
                    
                    eval_conc = ''
                    for ev_val in eval_dict:
                        eval_conc = eval_conc + eval_dict[ev_val]
                    
                    if str(eval_sort[0]).startswith('#') or str(move_eval).startswith('#'):
                        cp_loss = ''.ljust(6, ' ')
                    else:
                        cp_loss = str(round(abs(eval_sort[0] - move_eval), 2)).ljust(6, ' ')
                    
                    move = move.ljust(7, ' ')
                    move_eval = str(move_eval).ljust(6, ' ')
                    gmid = str(gameid).ljust(10, ' ')
                    dp = str(d).ljust(2, ' ')
                    fen = board.fen().ljust(92, ' ')
        
                    # RECORD 02: MOVE ANALYSIS
                    with open(full_output, 'a') as f:
                        f.write('02' + gmid + movenum + color + istheory + istablebase +
                            move + mv_conc + move_eval + eval_conc + cp_loss +
                            eng + dp + e_time + fen + clk + pgn_eval + row_delim)
                    
                    board.push(mv)
                else:
                    istablebase = '1'
                    tbresults = tbsearch(fen)
                    k = 0
                    while True:
                        if tbresults[k][0] == board.san(mv):
                            idx = k
                            break
                        k = k + 1
                    if board.turn:
                        color = 'White'
                    else:
                        color = 'Black'
                    
                    gmid = str(gameid).ljust(10, ' ')
                    movenum = str(board.fullmove_number).ljust(3, ' ')
                    move = board.san(mv).ljust(7, ' ')
                    move_eval = tbeval(tbresults[idx]).ljust(6, ' ')
                    dp = 'TB'
                    fen = board.fen().ljust(92, ' ')
                    cp_loss = ''.ljust(6, ' ')
                    
                    logging.info(f'{ctr} {gameid} {color} {board.fullmove_number}')

                    e_time = str(round(time.time() - s_time, 4)).ljust(8, ' ')
                    
                    move_dict = {'T' + str(ii + 1):  ''.ljust(7, ' ') for ii in range(32)}
                    eval_dict = {'T' + str(ii + 1) + '_Eval':  ''.ljust(6, ' ') for ii in range(32)}

                    mv_iter = 32 if len(tbresults) >= 32 else len(tbresults)
                    for i in range(mv_iter):
                        tmp_move = str(tbresults[i][0]).ljust(7, ' ')
                        tmp_eval = tbeval(tbresults[i]).ljust(6, ' ')
                        move_dict.update({'T' + str(i + 1): tmp_move})
                        eval_dict.update({'T' + str(i + 1) + '_Eval': tmp_eval})
                    
                    mv_conc = ''
                    for mv_val in move_dict:
                        mv_conc = mv_conc + move_dict[mv_val]
                    
                    eval_conc = ''
                    for ev_val in eval_dict:
                        eval_conc = eval_conc + eval_dict[ev_val]                        
        
                    # RECORD 02: MOVE ANALYSIS
                    with open(full_output, 'a') as f:
                        f.write('02' + gmid + movenum + color + istheory + istablebase +
                            move + mv_conc + move_eval + eval_conc + cp_loss +
                            eng + dp + e_time + fen + clk + pgn_eval + row_delim)
                    
                    board.push(mv)
                        
            logging.info(f"Completed processing game {ctr} at {dt.datetime.now().strftime('%H:%M:%S')}")
            gameid = gameid + 1

        game_text = chess.pgn.read_game(pgn)
        ctr = ctr + 1
        
    engine.quit()
    pgn.close()
    logging.info(f"END PROCESSING: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
