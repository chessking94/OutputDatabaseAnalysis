import datetime as dt
import json
import logging
import math
import os
import time

import chess
import chess.engine
import chess.pgn
import pandas as pd
import pyodbc as sql
import requests


def get_connstr():
    # get SQL Server connection string from private file
    fpath = r'C:\Users\eehunt\Repository'
    fname = 'confidential.json'
    with open(os.path.join(fpath, fname), 'r') as t:
        key_data = json.load(t)
    conn_str = key_data.get('SqlServerConnectionStringTrusted')
    return conn_str

def getlichesstoken():
    fpath = r'C:\Users\eehunt\Repository'
    fname = 'confidential.json'
    with open(os.path.join(fpath, fname), 'r') as t:
        key_data = json.load(t)
    token_value = key_data.get('LichessAPIToken')
    return token_value

def bookmoves(fen, date):
    token_value = getlichesstoken()

    base_url = 'https://explorer.lichess.ovh/lichess?variant=standard&speeds=rapid,classical,correspondence&ratings=2000,2200,2500&fen='
    url = base_url + fen.replace(' ', '_')
    if date is not None: # this check is in place to essentially avoid my own Lichess games from being referenced in the explorer API
        url = url + '&until=' + date

    hdr = {'Authorization': 'Bearer ' + token_value}
    cde = 429
    while cde != 200:
        with requests.get(url, headers=hdr) as resp:
            cde = resp.status_code
            theory = []
            ct = 0
            if cde == 200:
                book_results = json.loads(resp.content)
                for mv in book_results['moves']:
                    theory.append(mv['san'])
            else:
                ct = ct + 1
                if cde == 429:
                    logging.info('API returned 429, waiting 65 seconds before trying again')
                    time.sleep(65)
                else:
                    logging.info(f'API returned {cde}, skipped FEN {fen}')
            
            if ct == 5: # exit ability to avoid infinite loop
                logging.info('API rejected 5 consecutive times, skipping!')
                cde = 200
    
    return theory

def piececount(fen):
    end = fen.find(' ', 1)
    brd = fen[0:end]
    ct = 0
    for x in brd:
        if x.isalpha():
            ct = ct + 1
    return ct

def tbsearch(fen):
    token_value = getlichesstoken()

    base_url = 'http://tablebase.lichess.ovh/standard?fen='
    url = base_url + fen.replace(' ', '_')

    hdr = {'Authorization': 'Bearer ' + token_value}
    cde = 429
    while cde != 200:
        with requests.get(url, headers=hdr) as resp:
            cde = resp.status_code
            info = []
            ct = 0
            if cde == 200:
                tb_results = json.loads(resp.content)
                info = []
                i = len(tb_results['moves'])
                j = 0
                while j < i:
                    tbmove = []

                    # san move
                    tbmove.append(tb_results['moves'][j]['san'])

                    # dtm
                    m = tb_results['moves'][j]['dtm']
                    if m is not None:
                        if m < 0:
                            m = m - 1
                            if fen.find('w', 0) >= 0:
                                m = m * (-1)
                            m = math.floor(m/2)
                        elif m > 0:
                            m = int(m) + 1
                            if fen.find('w', 0) >= 0:
                                m = m * (-1)
                            m = math.ceil(m/2)
                        else:
                            pass
                        m = str(m)
                    tbmove.append(m)

                    # dtz
                    z = tb_results['moves'][j]['dtz']
                    if z is not None:
                        if z < 0: # winning
                            z = z - 1
                            if fen.find('w', 0) >= 0:
                                z = z * (-1)
                            z = math.floor(z/2)
                        elif z > 0:
                            z = z + 1
                            if fen.find('w', 0) >= 0:
                                z = z * (-1)
                            z = math.ceil(z/2)
                        else:
                            pass
                        z = str(z)
                    tbmove.append(z)

                    info.append(tbmove)
                    j = j + 1
            else:
                ct = ct + 1
                if cde == 429:
                    logging.info('API returned 429, waiting 65 seconds before trying again')
                    time.sleep(65)
                else:
                    logging.info(f'API returned {cde}, skipped FEN {fen}')
            
            if ct == 5: # exit ability to avoid infinite loop
                logging.info('API rejected 5 consecutive times, skipping!')
                cde = 200             

    return info

def tbeval(tbdata):
    # returns #-n, #+n, #+nZ, and #-nZ
    if tbdata[1] is not None: # DTM populated, takes priority
        if tbdata[1] == '0':
            sc = '0.00'
        else:
            sc = '#' + tbdata[1] if tbdata[1].find('-') >= 0 else '#+' + tbdata[1]
    else:
        if tbdata[2] == '0':
            sc = '0.00'
        else:
            sc = '#' + tbdata[2] + 'Z' if tbdata[2].find('-') >= 0 else '#+' + tbdata[2] + 'Z'
    return sc

def format_tournament(game_text, tag):
    tag_text = game_text.headers.get(tag)
    tmnt_len = 50
    tmnt = ''.ljust(tmnt_len, ' ')

    if tag_text is not None:
        tmnt = tag_text.ljust(tmnt_len, ' ')
    
    return tmnt

def format_name(game_text, tag):
    tag_text = game_text.headers.get(tag)
    ret_arr = []
    lname, fname = '', ''
    lname_len, fname_len = 50, 25

    if tag_text is not None:
        if tag_text.find(',', 1) >= 0:
            lname, fname = tag_text.split(',', 2)
            lname = lname.strip().ljust(lname_len, ' ')
            fname = fname.strip().ljust(fname_len, ' ')
        else:
            lname = tag_text.strip().ljust(lname_len, ' ')
            fname = fname_len*' '
            fname = fname.ljust(fname_len, ' ')
    
    ret_arr.append(lname)
    ret_arr.append(fname)
    return ret_arr

def format_elo(game_text, tag):
    tag_text = game_text.headers.get(tag)
    elo_len = 4
    elo = ''.ljust(elo_len, ' ')

    if tag_text is not None:
        elo = tag_text.ljust(elo_len, ' ')
    
    return elo

def format_date(game_text, tag):
    tag_text = game_text.headers.get(tag)
    dte_arr = []
    dte_len = 10
    dte = ''.ljust(dte_len, ' ')
    dte_val = None

    if tag_text is not None:
        dte = tag_text.ljust(dte_len, ' ')
        if dte.find('??') > 0: # replace any missing date parts
            logging.warning(f'Missing date parts: {dte}')
            dte = dte.replace('??', '01')
        yr, mo = int(dte[0:4]), int(dte[5:7])
        if mo == 1:
            yr, mo = str(yr - 1), '12'
        else:
            yr, mo = str(yr), mo - 1
            mo = '0' + str(mo) if mo < 10 else str(mo)
        dte_val = yr + '-' + mo
    
    dte_arr.append(dte)
    dte_arr.append(dte_val)
    return dte_arr

def format_round(game_text, tag):
    tag_text = game_text.headers.get(tag)
    rd_len = 7
    rd = '?'.ljust(rd_len, ' ')

    if tag_text is not None:
        rd = tag_text.ljust(rd_len, ' ')
        rd = rd.replace('-', '?')
    
    return rd

def format_eco(game_text, tag):
    tag_text = game_text.headers.get(tag)
    eco_len = 3
    eco = ''.ljust(eco_len, ' ')

    if tag_text is not None:
        eco = tag_text.ljust(eco_len, ' ')
    
    return eco

def format_result(game_text, tag):
    tag_text = game_text.headers.get(tag)
    res_len = 3
    res = ''

    if tag_text is not None:
        if tag_text == '1-0':
            res = '1.0'
        elif tag_text == '0-1':
            res = '0.0'
        elif tag_text == '1/2-1/2':
            res = '0.5'
    
    res = res.ljust(res_len, ' ')
    return res

def format_moves(game_text, tag):
    tag_text = game_text.headers.get(tag)
    mv_len = 3
    mv = ''.ljust(mv_len, ' ')

    if tag_text is not None:
        mv = str(math.ceil(int(tag_text)/2)).ljust(mv_len, ' ')
    
    return mv

def format_source_id(game_text, tag):
    tag_text = game_text.headers.get(tag)
    site_arr = []
    site_len, site_id_len = 15, 20
    site, site_id = ''.ljust(site_len, ' '), ''.ljust(site_id_len, ' ')

    if tag_text is not None:
        if tag_text.find('lichess', 0) >= 0:
            site = 'Lichess'.ljust(site_len, ' ')
            site_id = tag_text.split('/')[-1].ljust(site_id_len, ' ')
        elif tag_text.find('Chess.com', 0) >= 0:
            site = 'Chess.com'.ljust(site_len, ' ')
            lnk = game_text.headers.get('Link')
            if lnk is not None:
                site_id = lnk.split('/')[-1].ljust(site_id_len, ' ')
        elif tag_text.find('FICS', 0) >= 0:
            site = 'FICS'.ljust(site_len, ' ')
            site_id = game_text.headers.get('FICSGamesDBGameNo').ljust(site_id_len, ' ')
    
    site_arr.append(site)
    site_arr.append(site_id)
    return site_arr

def format_timecontrol(game_text, tag):
    tag_text = game_text.headers.get(tag)
    tc_len = 15
    tc = ''.ljust(tc_len, ' ')

    if tag_text is not None:
        tc = tag_text.ljust(tc_len, ' ')
    
    return tc

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

    game_type = 'Online'
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
        tournament = format_tournament(game_text, 'Event')
        whitelast, whitefirst = format_name(game_text, 'White')
        blacklast, blackfirst = format_name(game_text, 'Black')
        whiteelo = format_elo(game_text, 'WhiteElo')
        blackelo = format_elo(game_text, 'BlackElo')
        roundnum = format_round(game_text, 'Round')
        eco = format_eco(game_text, 'ECO')
        gamedate, date_val = format_date(game_text, 'Date')
        result = format_result(game_text, 'Result')
        moves = format_moves(game_text, 'PlyCount')
        src, srcid = format_source_id(game_text, 'Site')
        tmctrl = format_timecontrol(game_text, 'TimeControl')
        
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
                # TODO: Implement eval comment parsing, likely need to handle mates carefully like below
                # pgn_eval = str(round(node.eval().white().score()/100., 2))
                
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
                            eng + dp + e_time + fen + clk + row_delim)
                    
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
                            eng + dp + e_time + fen + clk + row_delim)
                    
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
