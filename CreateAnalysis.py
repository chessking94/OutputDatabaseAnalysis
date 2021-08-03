import chess
import chess.pgn
import chess.engine
import os
import math
import time as t
import pyodbc as sql
import datetime as dt
from urllib import request
import chess.polyglot

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
    html = str(request.urlopen(url + fen2).read())
    start = html.find('[', 1) + 1
    end = len(html) - 1
    data = html[start:end]
    info = []
    x = 0
    y = 1
    while x < y:
        tbmove = []
        # uci move
        t_start = data.find('uci', x) + 6
        t_end = data.find('"', t_start)
        tbmove.append(data[t_start:t_end])
        x = t_end
        
        # san move
        t_start = data.find('san', x) + 6
        t_end = data.find('"', t_start)
        tbmove.append(data[t_start:t_end])
        x = t_end
        
        # dtm
        t_start = data.find('dtm', x) + 5
        t_end = data.find('}', t_start)
        if data[t_start:t_end].find('-') >= 0:
            m = int(data[t_start:t_end]) - 1
            if fen.find('w', 1) >= 0:
                m = m * (-1)
            m = math.floor(m/2)
            tbmove.append(str(m))
        elif data[t_start:t_end] != '0':
            m = int(data[t_start:t_end]) + 1
            if fen.find('w', 1) >= 0:
                m = m * (-1)
            m = math.ceil(m/2)
            tbmove.append(str(m))
        else:
            tbmove.append(data[t_start:t_end])
        x = t_end
        y = data.find('uci', x) + 6
        info.append(tbmove)
    
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
    d = 11 # depth
    prog = 1 # flag to list move-by-move progress
    corrflag = '0' # flag if the PGN being processed is correspondence games
    db = 1 # use database to get next GameID val
    db_name = 'OnlineGames' # database name
    control_flag = 0 # determines file paths
    pgn_name = 'NefariousNebula_202107_Cleaned' # name of file

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
        conn = sql.connect('Driver={ODBC Driver 17 for SQL Server};Server=HUNT-PC1;'
                            'Database=ChessAnalysis;Trusted_Connection=yes;')
        csr = conn.cursor()
        
        qry_text = "SELECT IDENT_CURRENT('" + db_name + "') + 1 AS GameID"
        csr.execute(qry_text)
        gameid = csr.fetchone()[0]
        conn.close()
    else:
        gameid = 1 # hard code first gameid, if necessary
    print('Current GameID:' + str(gameid))

    print('BEGIN PROCESSING: ' + dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ctr = 0
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
                
                if piececount(fen) > 5: # 7-piece tablebases are available, but freely distributed syzergy files don't have DTM data; only Lomonosov
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

                    if board.turn:
                        move_sort = [x for _, x in sorted(zip(eval_properA, move_list), reverse=True)]
                        eval_sort = [y for _, y in sorted(zip(eval_properA, eval_list), reverse=True)]
                        eval_properB = sorted(eval_properA, reverse=True)
                    else:
                        move_sort = [x for _, x in sorted(zip(eval_properA, move_list), reverse=False)]
                        eval_sort = [y for _, y in sorted(zip(eval_properA, eval_list), reverse=False)]
                        eval_properB = sorted(eval_properA)
                            
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
                    # there is probably a more efficient way to do the below, but it works for now
                    try:
                        t1 = str(move_sort[0]) + 7*' '
                        t1_eval = str(eval_sort[0]) + 6*' '
                        t1 = t1[0:7]
                        t1_eval = t1_eval[0:6]
                    except IndexError:
                        t1 = 7*' '
                        t1_eval = 6*' '
                    try:
                        t2 = str(move_sort[1]) + 7*' '
                        t2_eval = str(eval_sort[1]) + 6*' '
                        t2 = t2[0:7]
                        t2_eval = t2_eval[0:6]
                    except IndexError:
                        t2 = 7*' '
                        t2_eval = 6*' '
                    try:
                        t3 = str(move_sort[2]) + 7*' '
                        t3_eval = str(eval_sort[2]) + 6*' '
                        t3 = t3[0:7]
                        t3_eval = t3_eval[0:6]
                    except IndexError:
                        t3 = 7*' '
                        t3_eval = 6*' '
                    try:
                        t4 = str(move_sort[3]) + 7*' '
                        t4_eval = str(eval_sort[3]) + 6*' '
                        t4 = t4[0:7]
                        t4_eval = t4_eval[0:6]
                    except IndexError:
                        t4 = 7*' '
                        t4_eval = 6*' '
                    try:
                        t5 = str(move_sort[4]) + 7*' '
                        t5_eval = str(eval_sort[4]) + 6*' '
                        t5 = t5[0:7]
                        t5_eval = t5_eval[0:6]
                    except IndexError:
                        t5 = 7*' '
                        t5_eval = 6*' '
                    try:
                        t6 = str(move_sort[5]) + 7*' '
                        t6_eval = str(eval_sort[5]) + 6*' '
                        t6 = t6[0:7]
                        t6_eval = t6_eval[0:6]
                    except IndexError:
                        t6 = 7*' '
                        t6_eval = 6*' '
                    try:
                        t7 = str(move_sort[6]) + 7*' '
                        t7_eval = str(eval_sort[6]) + 6*' '
                        t7 = t7[0:7]
                        t7_eval = t7_eval[0:6]
                    except IndexError:
                        t7 = 7*' '
                        t7_eval = 6*' '
                    try:
                        t8 = str(move_sort[7]) + 7*' '
                        t8_eval = str(eval_sort[7]) + 6*' '
                        t8 = t8[0:7]
                        t8_eval = t8_eval[0:6]
                    except IndexError:
                        t8 = 7*' '
                        t8_eval = 6*' '
                    try:
                        t9 = str(move_sort[8]) + 7*' '
                        t9_eval = str(eval_sort[8]) + 6*' '
                        t9 = t9[0:7]
                        t9_eval = t9_eval[0:6]
                    except IndexError:
                        t9 = 7*' '
                        t9_eval = 6*' '
                    try:
                        t10 = str(move_sort[9]) + 7*' '
                        t10_eval = str(eval_sort[9]) + 6*' '
                        t10 = t10[0:7]
                        t10_eval = t10_eval[0:6]
                    except IndexError:
                        t10 = 7*' '
                        t10_eval = 6*' '
                    try:
                        t11 = str(move_sort[10]) + 7*' '
                        t11_eval = str(eval_sort[10]) + 6*' '
                        t11 = t11[0:7]
                        t11_eval = t11_eval[0:6]
                    except IndexError:
                        t11 = 7*' '
                        t11_eval = 6*' '
                    try:
                        t12 = str(move_sort[11]) + 7*' '
                        t12_eval = str(eval_sort[11]) + 6*' '
                        t12 = t12[0:7]
                        t12_eval = t12_eval[0:6]
                    except IndexError:
                        t12 = 7*' '
                        t12_eval = 6*' '
                    try:
                        t13 = str(move_sort[12]) + 7*' '
                        t13_eval = str(eval_sort[12]) + 6*' '
                        t13 = t13[0:7]
                        t13_eval = t13_eval[0:6]
                    except IndexError:
                        t13 = 7*' '
                        t13_eval = 6*' '
                    try:
                        t14 = str(move_sort[13]) + 7*' '
                        t14_eval = str(eval_sort[13]) + 6*' '
                        t14 = t14[0:7]
                        t14_eval = t14_eval[0:6]
                    except IndexError:
                        t14 = 7*' '
                        t14_eval = 6*' '
                    try:
                        t15 = str(move_sort[14]) + 7*' '
                        t15_eval = str(eval_sort[14]) + 6*' '
                        t15 = t15[0:7]
                        t15_eval = t15_eval[0:6]
                    except IndexError:
                        t15 = 7*' '
                        t15_eval = 6*' '
                    try:
                        t16 = str(move_sort[15]) + 7*' '
                        t16_eval = str(eval_sort[15]) + 6*' '
                        t16 = t16[0:7]
                        t16_eval = t16_eval[0:6]
                    except IndexError:
                        t16 = 7*' '
                        t16_eval = 6*' '
                    try:
                        t17 = str(move_sort[16]) + 7*' '
                        t17_eval = str(eval_sort[16]) + 6*' '
                        t17 = t17[0:7]
                        t17_eval = t17_eval[0:6]
                    except IndexError:
                        t17 = 7*' '
                        t17_eval = 6*' '
                    try:
                        t18 = str(move_sort[17]) + 7*' '
                        t18_eval = str(eval_sort[17]) + 6*' '
                        t18 = t18[0:7]
                        t18_eval = t18_eval[0:6]
                    except IndexError:
                        t18 = 7*' '
                        t18_eval = 6*' '
                    try:
                        t19 = str(move_sort[18]) + 7*' '
                        t19_eval = str(eval_sort[18]) + 6*' '
                        t19 = t19[0:7]
                        t19_eval = t19_eval[0:6]
                    except IndexError:
                        t19 = 7*' '
                        t19_eval = 6*' '
                    try:
                        t20 = str(move_sort[19]) + 7*' '
                        t20_eval = str(eval_sort[19]) + 6*' '
                        t20 = t20[0:7]
                        t20_eval = t20_eval[0:6]
                    except IndexError:
                        t20 = 7*' '
                        t20_eval = 6*' '
                    try:
                        t21 = str(move_sort[20]) + 7*' '
                        t21_eval = str(eval_sort[20]) + 6*' '
                        t21 = t21[0:7]
                        t21_eval = t21_eval[0:6]
                    except IndexError:
                        t21 = 7*' '
                        t21_eval = 6*' '
                    try:
                        t22 = str(move_sort[21]) + 7*' '
                        t22_eval = str(eval_sort[21]) + 6*' '
                        t22 = t22[0:7]
                        t22_eval = t22_eval[0:6]
                    except IndexError:
                        t22 = 7*' '
                        t22_eval = 6*' '
                    try:
                        t23 = str(move_sort[22]) + 7*' '
                        t23_eval = str(eval_sort[22]) + 6*' '
                        t23 = t23[0:7]
                        t23_eval = t23_eval[0:6]
                    except IndexError:
                        t23 = 7*' '
                        t23_eval = 6*' '
                    try:
                        t24 = str(move_sort[23]) + 7*' '
                        t24_eval = str(eval_sort[23]) + 6*' '
                        t24 = t24[0:7]
                        t24_eval = t24_eval[0:6]
                    except IndexError:
                        t24 = 7*' '
                        t24_eval = 6*' '
                    try:
                        t25 = str(move_sort[24]) + 7*' '
                        t25_eval = str(eval_sort[24]) + 6*' '
                        t25 = t25[0:7]
                        t25_eval = t25_eval[0:6]
                    except IndexError:
                        t25 = 7*' '
                        t25_eval = 6*' '
                    try:
                        t26 = str(move_sort[25]) + 7*' '
                        t26_eval = str(eval_sort[25]) + 6*' '
                        t26 = t26[0:7]
                        t26_eval = t26_eval[0:6]
                    except IndexError:
                        t26 = 7*' '
                        t26_eval = 6*' '
                    try:
                        t27 = str(move_sort[26]) + 7*' '
                        t27_eval = str(eval_sort[26]) + 6*' '
                        t27 = t27[0:7]
                        t27_eval = t27_eval[0:6]
                    except IndexError:
                        t27 = 7*' '
                        t27_eval = 6*' '
                    try:
                        t28 = str(move_sort[27]) + 7*' '
                        t28_eval = str(eval_sort[27]) + 6*' '
                        t28 = t28[0:7]
                        t28_eval = t28_eval[0:6]
                    except IndexError:
                        t28 = 7*' '
                        t28_eval = 6*' '
                    try:
                        t29 = str(move_sort[28]) + 7*' '
                        t29_eval = str(eval_sort[28]) + 6*' '
                        t29 = t29[0:7]
                        t29_eval = t29_eval[0:6]
                    except IndexError:
                        t29 = 7*' '
                        t29_eval = 6*' '
                    try:
                        t30 = str(move_sort[29]) + 7*' '
                        t30_eval = str(eval_sort[29]) + 6*' '
                        t30 = t30[0:7]
                        t30_eval = t30_eval[0:6]
                    except IndexError:
                        t30 = 7*' '
                        t30_eval = 6*' '
                    try:
                        t31 = str(move_sort[30]) + 7*' '
                        t31_eval = str(eval_sort[30]) + 6*' '
                        t31 = t31[0:7]
                        t31_eval = t31_eval[0:6]
                    except IndexError:
                        t31 = 7*' '
                        t31_eval = 6*' ' 
                    try:
                        t32 = str(move_sort[31]) + 7*' '
                        t32_eval = str(eval_sort[31]) + 6*' '
                        t32 = t32[0:7]
                        t32_eval = t32_eval[0:6]
                    except IndexError:
                        t32 = 7*' '
                        t32_eval = 6*' '
                    try:
                        if str(eval_sort[0]).startswith('#') or str(move_eval).startswith('#'):
                            cp_loss = 6*' '
                        else:
                            cp_loss = str(round(abs(eval_sort[0] - move_eval), 2)) + 6*' '
                            cp_loss = cp_loss[0:6]
                    except IndexError:
                        cp_loss = 6*' '
                    
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
                        move + t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8 + t9 + t10 +
                        t11 + t12 + t13 + t14 + t15 + t16 + t17 + t18 + t19 + t20 +
                        t21 + t22 + t23 + t24 + t25 + t26 + t27 + t28 + t29 + t30 +
                        t31 + t32 + move_eval +
                        t1_eval + t2_eval + t3_eval + t4_eval + t5_eval +
                        t6_eval + t7_eval + t8_eval + t9_eval + t10_eval +
                        t11_eval + t12_eval + t13_eval + t14_eval + t15_eval +
                        t16_eval + t17_eval + t18_eval + t19_eval + t20_eval +
                        t21_eval + t22_eval + t23_eval + t24_eval + t25_eval +
                        t26_eval + t27_eval + t28_eval + t29_eval + t30_eval +
                        t31_eval + t32_eval + cp_loss +
                        eng + dp + e_time + fen + row_delim)
                    
                    board.push(mv)
                else:
                    istablebase = '1'
                    try:
                        tbresults = tbsearch(fen)
                    except:
                        t.sleep(75)
                        tbresults = tbsearch(fen)
                    k = 0
                    for sc in tbresults:
                        if tbresults[k][1] == board.san(mv):
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
                    if tbresults[idx][2] == '0':
                        move_eval = '0.00' + 6*' '
                        move_eval = move_eval[0:6]
                    else:
                        if tbresults[idx][2].find('-') >= 0:
                            move_eval = '#' + tbresults[idx][2] + 6*' '
                            move_eval = move_eval[0:6]
                        else:
                            move_eval = '#+' + tbresults[idx][2] + 6*' '
                            move_eval = move_eval[0:6]
                    dp = 'TB' # may change
                    fen = board.fen() + 92*' '
                    fen = fen[0:92]
                    cp_loss = 6*' '
                    
                    if prog == 1:
                        print(str(ctr), str(gameid), color, board.fullmove_number)

                    e_time = str(round(t.time() - s_time, 4)) + 8*' '
                    e_time = e_time[0:8]
                    
                    try:
                        t1 = tbresults[0][1] + 7*' '
                        t1_eval = tbeval(tbresults[0][2]) + 6*' '
                        t1 = t1[0:7]
                        t1_eval = t1_eval[0:6]
                    except:
                        t1 = 7*' '
                        t1_eval = 6*' '
                    try:
                        t2 = tbresults[1][1] + 7*' '
                        t2_eval = tbeval(tbresults[1][2]) + 6*' '
                        t2 = t2[0:7]
                        t2_eval = t2_eval[0:6]
                    except:
                        t2 = 7*' '
                        t2_eval = 6*' '
                    try:
                        t3 = tbresults[2][1] + 7*' '
                        t3_eval = tbeval(tbresults[2][2]) + 6*' '
                        t3 = t3[0:7]
                        t3_eval = t3_eval[0:6]
                    except:
                        t3 = 7*' '
                        t3_eval = 6*' '
                    try:
                        t4 = tbresults[3][1] + 7*' '
                        t4_eval = tbeval(tbresults[3][2]) + 6*' '
                        t4 = t4[0:7]
                        t4_eval = t4_eval[0:6]
                    except:
                        t4 = 7*' '
                        t4_eval = 6*' '
                    try:
                        t5 = tbresults[4][1] + 7*' '
                        t5_eval = tbeval(tbresults[4][2]) + 6*' '
                        t5 = t5[0:7]
                        t5_eval = t5_eval[0:6]
                    except:
                        t5 = 7*' '
                        t5_eval = 6*' '
                    try:
                        t6 = tbresults[5][1] + 7*' '
                        t6_eval = tbeval(tbresults[5][2]) + 6*' '
                        t6 = t6[0:7]
                        t6_eval = t6_eval[0:6]
                    except:
                        t6 = 7*' '
                        t6_eval = 6*' '
                    try:
                        t7 = tbresults[6][1] + 7*' '
                        t7_eval = tbeval(tbresults[6][2]) + 6*' '
                        t7 = t7[0:7]
                        t7_eval = t7_eval[0:6]
                    except:
                        t7 = 7*' '
                        t7_eval = 6*' '
                    try:
                        t8 = tbresults[7][1] + 7*' '
                        t8_eval = tbeval(tbresults[7][2]) + 6*' '
                        t8 = t8[0:7]
                        t8_eval = t8_eval[0:6]
                    except:
                        t8 = 7*' '
                        t8_eval = 6*' '
                    try:
                        t9 = tbresults[8][1] + 7*' '
                        t9_eval = tbeval(tbresults[8][2]) + 6*' '
                        t9 = t9[0:7]
                        t9_eval = t9_eval[0:6]
                    except:
                        t9 = 7*' '
                        t9_eval = 6*' '
                    try:
                        t10 = tbresults[9][1] + 7*' '
                        t10_eval = tbeval(tbresults[9][2]) + 6*' '
                        t10 = t10[0:7]
                        t10_eval = t10_eval[0:6]
                    except:
                        t10 = 7*' '
                        t10_eval = 6*' '
                    try:
                        t11 = tbresults[10][1] + 7*' '
                        t11_eval = tbeval(tbresults[10][2]) + 6*' '
                        t11 = t11[0:7]
                        t11_eval = t11_eval[0:6]
                    except:
                        t11 = 7*' '
                        t11_eval = 6*' '
                    try:
                        t12 = tbresults[11][1] + 7*' '
                        t12_eval = tbeval(tbresults[11][2]) + 6*' '
                        t12 = t12[0:7]
                        t12_eval = t12_eval[0:6]
                    except:
                        t12 = 7*' '
                        t12_eval = 6*' '
                    try:
                        t13 = tbresults[12][1] + 7*' '
                        t13_eval = tbeval(tbresults[12][2]) + 6*' '
                        t13 = t13[0:7]
                        t13_eval = t13_eval[0:6]
                    except:
                        t13 = 7*' '
                        t13_eval = 6*' '
                    try:
                        t14 = tbresults[13][1] + 7*' '
                        t14_eval = tbeval(tbresults[13][2]) + 6*' '
                        t14 = t14[0:7]
                        t14_eval = t14_eval[0:6]
                    except:
                        t14 = 7*' '
                        t14_eval = 6*' '
                    try:
                        t15 = tbresults[14][1] + 7*' '
                        t15_eval = tbeval(tbresults[14][2]) + 6*' '
                        t15 = t15[0:7]
                        t15_eval = t15_eval[0:6]
                    except:
                        t15 = 7*' '
                        t15_eval = 6*' '
                    try:
                        t16 = tbresults[15][1] + 7*' '
                        t16_eval = tbeval(tbresults[15][2]) + 6*' '
                        t16 = t16[0:7]
                        t16_eval = t16_eval[0:6]
                    except:
                        t16 = 7*' '
                        t16_eval = 6*' '
                    try:
                        t17 = tbresults[16][1] + 7*' '
                        t17_eval = tbeval(tbresults[16][2]) + 6*' '
                        t17 = t17[0:7]
                        t17_eval = t17_eval[0:6]
                    except:
                        t17 = 7*' '
                        t17_eval = 6*' '
                    try:
                        t18 = tbresults[17][1] + 7*' '
                        t18_eval = tbeval(tbresults[17][2]) + 6*' '
                        t18 = t18[0:7]
                        t18_eval = t18_eval[0:6]
                    except:
                        t18 = 7*' '
                        t18_eval = 6*' '
                    try:
                        t19 = tbresults[18][1] + 7*' '
                        t19_eval = tbeval(tbresults[18][2]) + 6*' '
                        t19 = t19[0:7]
                        t19_eval = t19_eval[0:6]
                    except:
                        t19 = 7*' '
                        t19_eval = 6*' '
                    try:
                        t20 = tbresults[19][1] + 7*' '
                        t20_eval = tbeval(tbresults[19][2]) + 6*' '
                        t20 = t20[0:7]
                        t20_eval = t20_eval[0:6]
                    except:
                        t20 = 7*' '
                        t20_eval = 6*' '
                    try:
                        t21 = tbresults[20][1] + 7*' '
                        t21_eval = tbeval(tbresults[20][2]) + 6*' '
                        t21 = t21[0:7]
                        t21_eval = t21_eval[0:6]
                    except:
                        t21 = 7*' '
                        t21_eval = 6*' '
                    try:
                        t22 = tbresults[21][1] + 7*' '
                        t22_eval = tbeval(tbresults[21][2]) + 6*' '
                        t22 = t22[0:7]
                        t22_eval = t22_eval[0:6]
                    except:
                        t22 = 7*' '
                        t22_eval = 6*' '
                    try:
                        t23 = tbresults[22][1] + 7*' '
                        t23_eval = tbeval(tbresults[22][2]) + 6*' '
                        t23 = t23[0:7]
                        t23_eval = t23_eval[0:6]
                    except:
                        t23 = 7*' '
                        t23_eval = 6*' '
                    try:
                        t24 = tbresults[23][1] + 7*' '
                        t24_eval = tbeval(tbresults[23][2]) + 6*' '
                        t24 = t24[0:7]
                        t24_eval = t24_eval[0:6]
                    except:
                        t24 = 7*' '
                        t24_eval = 6*' '
                    try:
                        t25 = tbresults[24][1] + 7*' '
                        t25_eval = tbeval(tbresults[24][2]) + 6*' '
                        t25 = t25[0:7]
                        t25_eval = t25_eval[0:6]
                    except:
                        t25 = 7*' '
                        t25_eval = 6*' '
                    try:
                        t26 = tbresults[25][1] + 7*' '
                        t26_eval = tbeval(tbresults[25][2]) + 6*' '
                        t26 = t26[0:7]
                        t26_eval = t26_eval[0:6]
                    except:
                        t26 = 7*' '
                        t26_eval = 6*' '
                    try:
                        t27 = tbresults[26][1] + 7*' '
                        t27_eval = tbeval(tbresults[26][2]) + 6*' '
                        t27 = t27[0:7]
                        t27_eval = t27_eval[0:6]
                    except:
                        t27 = 7*' '
                        t27_eval = 6*' '
                    try:
                        t28 = tbresults[27][1] + 7*' '
                        t28_eval = tbeval(tbresults[27][2]) + 6*' '
                        t28 = t28[0:7]
                        t28_eval = t28_eval[0:6]
                    except:
                        t28 = 7*' '
                        t28_eval = 6*' '
                    try:
                        t29 = tbresults[28][1] + 7*' '
                        t29_eval = tbeval(tbresults[28][2]) + 6*' '
                        t29 = t29[0:7]
                        t29_eval = t29_eval[0:6]
                    except:
                        t29 = 7*' '
                        t29_eval = 6*' '
                    try:
                        t30 = tbresults[29][1] + 7*' '
                        t30_eval = tbeval(tbresults[29][2]) + 6*' '
                        t30 = t30[0:7]
                        t30_eval = t30_eval[0:6]
                    except:
                        t30 = 7*' '
                        t30_eval = 6*' '
                    try:
                        t31 = tbresults[30][1] + 7*' '
                        t31_eval = tbeval(tbresults[30][2]) + 6*' '
                        t31 = t31[0:7]
                        t31_eval = t31_eval[0:6]
                    except:
                        t31 = 7*' '
                        t31_eval = 6*' '
                    try:
                        t32 = tbresults[31][1] + 7*' '
                        t32_eval = tbeval(tbresults[31][2]) + 6*' '
                        t32 = t32[0:7]
                        t32_eval = t32_eval[0:6]
                    except:
                        t32 = 7*' '
                        t32_eval = 6*' '
                        
        
                    # RECORD 02: MOVE ANALYSIS
                    f.write('02' + gmid + movenum + color + istheory + istablebase +
                        move + t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8 + t9 + t10 +
                        t11 + t12 + t13 + t14 + t15 + t16 + t17 + t18 + t19 + t20 +
                        t21 + t22 + t23 + t24 + t25 + t26 + t27 + t28 + t29 + t30 +
                        t31 + t32 + move_eval +
                        t1_eval + t2_eval + t3_eval + t4_eval + t5_eval +
                        t6_eval + t7_eval + t8_eval + t9_eval + t10_eval +
                        t11_eval + t12_eval + t13_eval + t14_eval + t15_eval +
                        t16_eval + t17_eval + t18_eval + t19_eval + t20_eval +
                        t21_eval + t22_eval + t23_eval + t24_eval + t25_eval +
                        t26_eval + t27_eval + t28_eval + t29_eval + t30_eval +
                        t31_eval + t32_eval + cp_loss +
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