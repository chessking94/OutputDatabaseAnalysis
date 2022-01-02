import chess
import chess.pgn
import chess.engine
import os
import json
import math
import time as t
import pyodbc as sql
import datetime as dt
from urllib import request
import chess.polyglot
import pandas as pd

# function to generate list of moves in opening book
def bookmoves(fen):
    fpath = r'C:\Users\eehunt\Documents\Chess\Polyglot'
    fname = 'custom_book.bin'
    full_path = os.path.join(fpath, fname)
    board = chess.Board(fen)
    theory = []
    with chess.polyglot.open_reader(full_path) as reader:
        for entry in reader.find_all(board):
            mv = board.san(entry.move)
            theory.append(mv)
    return theory

# function to count number of pieces on the board
def piececount(fen):
    end = fen.find(' ', 1)
    brd = fen[0:end]
    ct = 0
    for x in brd:
        if x.isalpha():
            ct = ct + 1
    return ct

# function to return tablebase results
def tbsearch(fen):
    url = 'http://tablebase.lichess.ovh/standard?fen='
    fen2 = fen.replace(' ', '_')
    json_data = request.urlopen(url + fen2).read()
    tb_results = json.loads(json_data)
    info = []
    i = len(tb_results['moves'])
    j = 0
    while j < i:
        tbmove = []

        # san move
        tbmove.append(tb_results['moves'][j]['san'])

        # dtm
        m = tb_results['moves'][j]['dtm']
        if m < 0:
            m = m - 1
            if fen.find('w', 0) >= 0:
                m = m * (-1)
            m = math.floor(m/2)
        elif m != 0:
            m = int(m) + 1
            if fen.find('w', 0) >= 0:
                m = m * (-1)
            m = math.ceil(m/2)
        else:
            pass
        tbmove.append(str(m))

        info.append(tbmove)
        j = j + 1
    
    return info

def tbeval(k):
    if k == '0':
        sc = '0.00'
    else:
        if k.find('-') >= 0:
            sc = '#' + k
        else:
            sc = '#+' + k
    return sc

def main():
    # other parameters
    d = 15 # depth
    prog = 1 # flag to list move-by-move progress
    corrflag = '0' # flag if the PGN being processed is correspondence games
    db = 1 # use database to get next GameID val
    db_name = 'EEHGames' # database name
    control_flag = 0 # determines file paths
    pgn_name = 'ThK_20211223' # name of file

    # input/output stuff
    if control_flag == 1:
        pgn_path = r'C:\Users\eehunt\Documents\Chess\Engine Detection\Control Game Data\PGN'
        output_path = r'C:\Users\eehunt\Documents\Chess\Engine Detection\Control Game Data\Analysis Output'
    else:
        pgn_path = r'C:\Users\eehunt\Documents\Chess\Engine Detection\Player Analysis\PGN'
        output_path = r'C:\Users\eehunt\Documents\Chess\Engine Detection\Player Analysis\Analysis Output'
    full_pgn = os.path.join(pgn_path, pgn_name) + '.pgn'
    pgn = open(full_pgn)

    # analysis output declarations
    dte = dt.datetime.now().strftime('%Y%m%d%H%M%S')
    output_file = pgn_name + '_Processed_' + dte + '.txt'
    full_output = os.path.join(output_path, output_file)
    row_delim = '\n'

    # initiate engine
    engine_path = r'C:\Users\eehunt\Documents\Chess\ENGINES'
    engine_name = 'stockfish_11_x64'
    eng = engine_name + 25*' '
    eng = eng[0:25]
    engine = chess.engine.SimpleEngine.popen_uci(os.path.join(engine_path, engine_name))

    # initiate SQL connection
    if db == 1:
        conn = sql.connect('Driver={ODBC Driver 17 for SQL Server};Server=HUNT-PC1;Database=ChessAnalysis;Trusted_Connection=yes;')
        qry_text = "SELECT IDENT_CURRENT('" + db_name + "') + 1 AS GameID"
        qry_rec = pd.read_sql(qry_text, conn).values.tolist()
        gameid = int(qry_rec[0][0])
        conn.close()
    else:
        gameid = 1 # hard code first gameid, if necessary

    print('BEGIN PROCESSING: ' + dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ctr = 0
    """ Potentially could try and refactor out this for loop and use only chess.pgn.read_game(pgn), would need to review carefully """
    for gm in pgn:
        ctr = ctr + 1
        game_text = chess.pgn.read_game(pgn)
        board = chess.Board(chess.STARTING_FEN)
        try:
            tmnt_s = gm.find('"') + 1
            tmnt_e = gm.find('"', tmnt_s)
            tournament = gm[tmnt_s:tmnt_e] + 50*' '
            tournament = tournament[0:50]
        except:
            tournament = 50*' '
        try:
            whitelast = game_text.headers['White']
            if whitelast.find(',', 1) >= 0:
                whitelast, whitefirst = whitelast.split(',', 2)
                whitelast = whitelast.strip() + 50*' '
                whitefirst = whitefirst.strip() + 25*' '
                whitelast = whitelast[0:50]
                whitefirst = whitefirst[0:25]
            else:
                whitelast = whitelast.strip() + 50*' '
                whitelast = whitelast[0:50]
                whitefirst = 25*' '
        except:
            whitelast = ''
            whitefirst = ''
        try:
            blacklast = game_text.headers['Black']
            if blacklast.find(',', 1) >= 0:
                blacklast, blackfirst = blacklast.split(',', 2)
                blacklast = blacklast.strip() + 50*' '
                blackfirst = blackfirst.strip() + 25*' '
                blacklast = blacklast[0:50]
                blackfirst = blackfirst[0:25]
            else:
                blacklast = blacklast.strip() + 50*' '
                blacklast = blacklast[0:50]
                blackfirst = 25*' '
        except:
            blacklast = ''
            blackfirst = ''
        try:
            whiteelo = game_text.headers['WhiteElo'] + 4*' '
            whiteelo = whiteelo[0:4]
        except:
            whiteelo = 4*' '
        try:
            blackelo = game_text.headers['BlackElo'] + 4*' '
            blackelo = blackelo[0:4]
        except:
            blackelo = 4*' '
        try:
            roundnum = game_text.headers['Round'] + 7*' '
            if roundnum == '-' + 7*' ':
                roundnum = '?' + 7*' '
            roundnum = roundnum[0:7]
        except:
            roundnum = '?' + 7*' '
        try:
            eco = game_text.headers['ECO'] + 3*' '
            eco = eco[0:3]
        except:
            eco = 3* ' '
        try:
            gamedate = game_text.headers['Date'] + 10*' '
            gamedate = gamedate[0:10]
        except:
            gamedate = 10*' '
        try:
            result = game_text.headers['Result']
            if result == '1-0':
                result = '1.0'
            elif result == '0-1':
                result = '0.0'
            elif result == '1/2-1/2':
                result = '0.5'
            else:
                result = 3*' '
            result = result[0:3]
        except:
            result = 3*' '
        try: 
            moves = str(math.ceil(int(game_text.headers['PlyCount'])/2)) + 3*' '
            moves = moves[0:3]
        except:
            moves = 3*' '
        try:
            site = game_text.headers['Site']
            if site.find('lichess', 0) >= 0:
                src = 'Lichess' + 15*' '
            elif site.find('Chess.com', 0) >= 0:
                src = 'Chess.com' + 15*' '
            else:
                src = 15*' '
            src = src[0:15]
        except:
            src = 15*' '
        try:
            site = game_text.headers['Site']
            if site.find('lichess', 0) >= 0:
                srcid = site.split('/')[-1] + 20*' '
            elif site.find('Chess.com', 0) >= 0:
                try:
                    lnk = game_text.headers['Link']
                    srcid = lnk.split('/')[-1] + 20*' '
                except:
                    srcid = 20*' '
            else:
                srcid = 20*' '
            srcid = srcid[0:20]
        except:
            srcid = 20*' '
        try:
            tmctrl = game_text.headers['TimeControl'] + 15*' '
            tmctrl = tmctrl[0:15]
        except:
            tmctrl = 15*' '
        
        if whitelast == '' or blacklast == '':
            print('PGN game %d was missing names and not processed!' % (ctr))
        else:
            f = open(full_output, 'a')
            # RECORD 01: PRIMARY GAME INFORMATION
            f.write('01' + whitelast + whitefirst + whiteelo + blacklast + 
                    blackfirst + blackelo + eco + gamedate + tournament +
                    roundnum + result + moves + corrflag + src + srcid + tmctrl + row_delim)

            istheory = '1'
            for mv in game_text.mainline_moves():
                s_time = t.time()
                fen = board.fen()
                
                if istheory == '1':
                    if board.san(mv) not in bookmoves(fen):
                        istheory = '0'
                
                if piececount(fen) > 5: # 6/7-piece tablebases are available, but freely distributed syzergy files don't have DTM data; only Lomonosov
                    istablebase = '0'
                    if board.turn:
                        color = 'White'
                    else:
                        color = 'Black'
                    
                    eval_properA = []
                    eval_list = []
                    move_list = []
                    if prog == 1:
                        print(str(ctr), str(gameid), color, board.fullmove_number)
                    
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
                    
                    e_time = str(round(t.time() - s_time, 4)) + 8*' '
                    e_time = e_time[0:8]
                    
                    movenum = str(board.fullmove_number) + 3*' '
                    movenum = movenum[0:3]

                    # create dictionaries of moves and evals
                    move_dict = {'T' + str(ii + 1):  7*' ' for ii in range(32)}
                    eval_dict = {'T' + str(ii + 1) + '_Eval':  6*' ' for ii in range(32)}

                    mv_iter = 32 if len(move_sort) >= 32 else len(move_sort)
                    for i in range(mv_iter):
                        tmp_move = str(move_sort[i]) + 7*' '
                        tmp_eval = str(eval_sort[i]) + 6*' '
                        move_dict.update({'T' + str(i + 1): tmp_move[0:7]})
                        eval_dict.update({'T' + str(i + 1) + '_Eval': tmp_eval[0:6]})
                    
                    mv_conc = ''
                    for mv_val in move_dict:
                        mv_conc = mv_conc + move_dict[mv_val]
                    
                    eval_conc = ''
                    for ev_val in eval_dict:
                        eval_conc = eval_conc + eval_dict[ev_val]
                    
                    if str(eval_sort[0]).startswith('#') or str(move_eval).startswith('#'):
                        cp_loss = 6*' '
                    else:
                        cp_loss = str(round(abs(eval_sort[0] - move_eval), 2)) + 6*' '
                        cp_loss = cp_loss[0:6]
                    
                    move = move + 7*' '
                    move = move[0:7]
                    move_eval = str(move_eval) + 6*' '
                    move_eval = move_eval[0:6]
                    gmid = str(gameid) + 10*' '
                    gmid = gmid[0:10]
                    dp = str(d) + 2*' '
                    dp = dp[0:2]
                    fen = board.fen() + 92*' '
                    fen = fen[0:92]
        
                    # RECORD 02: MOVE ANALYSIS
                    f.write('02' + gmid + movenum + color + istheory + istablebase +
                        move + mv_conc + move_eval + eval_conc + cp_loss +
                        eng + dp + e_time + fen + row_delim)
                    
                    board.push(mv)
                else:
                    istablebase = '1'
                    try:
                        tbresults = tbsearch(fen)
                    except: # should only fail due to a 429 web request
                        t.sleep(75)
                        tbresults = tbsearch(fen)
                    k = 0
                    for sc in tbresults:
                        if tbresults[k][0] == board.san(mv):
                            idx = k
                        k = k + 1
                    if board.turn:
                        color = 'White'
                    else:
                        color = 'Black'
                    
                    gmid = str(gameid) + 10*' '
                    gmid = gmid[0:10]
                    movenum = str(board.fullmove_number) + 3*' '
                    movenum = movenum[0:3]
                    move = board.san(mv) + 7*' '
                    move = move[0:7]
                    if tbresults[idx][1] == '0':
                        move_eval = '0.00' + 6*' '
                        move_eval = move_eval[0:6]
                    else:
                        if tbresults[idx][1].find('-') >= 0:
                            move_eval = '#' + tbresults[idx][1] + 6*' '
                            move_eval = move_eval[0:6]
                        else:
                            move_eval = '#+' + tbresults[idx][1] + 6*' '
                            move_eval = move_eval[0:6]
                    dp = 'TB'
                    fen = board.fen() + 92*' '
                    fen = fen[0:92]
                    cp_loss = 6*' '
                    
                    if prog == 1:
                        print(str(ctr), str(gameid), color, board.fullmove_number)

                    e_time = str(round(t.time() - s_time, 4)) + 8*' '
                    e_time = e_time[0:8]
                    
                    move_dict = {'T' + str(ii + 1):  7*' ' for ii in range(32)}
                    eval_dict = {'T' + str(ii + 1) + '_Eval':  6*' ' for ii in range(32)}

                    mv_iter = 32 if len(tbresults) >= 32 else len(tbresults)
                    for i in range(mv_iter):
                        tmp_move = str(tbresults[i][0]) + 7*' '
                        tmp_eval = tbeval(str(tbresults[i][1])) + 6*' '
                        move_dict.update({'T' + str(i + 1): tmp_move[0:7]})
                        eval_dict.update({'T' + str(i + 1) + '_Eval': tmp_eval[0:6]})
                    
                    mv_conc = ''
                    for mv_val in move_dict:
                        mv_conc = mv_conc + move_dict[mv_val]
                    
                    eval_conc = ''
                    for ev_val in eval_dict:
                        eval_conc = eval_conc + eval_dict[ev_val]                        
        
                    # RECORD 02: MOVE ANALYSIS
                    f.write('02' + gmid + movenum + color + istheory + istablebase +
                        move + mv_conc + move_eval + eval_conc + cp_loss +
                        eng + dp + e_time + fen + row_delim)
                    
                    board.push(mv)
                        
            print('Completed processing game ' + str(ctr) + ' at ' + dt.datetime.now().strftime('%H:%M:%S'))
            gameid = gameid + 1
        f.flush()
    engine.quit()
    pgn.close()
    try:
        f.close()
    except:
        pass
    print('END PROCESSING: ' + dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == '__main__':
    main()