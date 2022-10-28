import logging
import re

import chess.engine


def calc_phase(fen, last_phs):
    # modeled off of Lichess' calulation; https://github.com/lichess-org/scalachess/blob/master/src/main/scala/Divider.scala
    fen_str = fen.split(' ')[0]
    majorsminors = len(re.findall('[nbrqNBRQ]', fen_str))
    bbr = fen_str.split('/')[0]
    wbr = fen_str.split('/')[-1]
    bbr_ct = len(re.findall('[nbrq]', bbr))
    wbr_ct = len(re.findall('[NBRQ]', wbr))

    if majorsminors <= 6 or last_phs == 3:
        return 3

    # lichess has a complicated other feature, I'm ignoring for now
    if majorsminors <= 10 or wbr_ct < 4 or bbr_ct < 4 or last_phs == 2:
        return 2

    return 1


def calc_timespent(prev_time, curr_time, incr):
    if prev_time is None or curr_time is None:
        if curr_time is None:
            return ''
        else:
            return 0
    ts = int(prev_time) - int(curr_time) + int(incr)
    if ts < 0:
        return 0
    else:
        return ts


def format_eval(eval):
    if eval.startswith('#'):
        rtn = int(eval[1:len(eval)])
        rtn = chess.engine.Mate(rtn)
    else:
        rtn = float(eval)
        rtn = round(int(rtn)/100., 2)

    return rtn


def get_date(game_text, tag):
    tag_text = game_text.headers.get(tag)
    dte_arr = []
    dte = ''
    dte_val = None

    # old Lichess games are missing the "Date" tag, use UTCDate instead
    if not tag_text:
        tag_text = game_text.headers.get('UTCDate')

    if tag_text:
        dte = tag_text
        if dte.find('??') > 0:  # replace any missing date parts
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


def get_name(game_text, tag):
    tag_text = game_text.headers.get(tag)
    ret_arr = []
    lname, fname = '', ''

    if tag_text is not None:
        if tag_text.find(',', 1) >= 0:
            lname, fname = tag_text.split(',', 2)
            lname = lname.strip()
            fname = fname.strip()
        else:
            lname = tag_text.strip()

    ret_arr.append(lname)
    ret_arr.append(fname)
    return ret_arr


def get_result(game_text, tag):
    tag_text = game_text.headers.get(tag)
    res = ''

    if tag_text is not None:
        if tag_text == '1-0':
            res = '1.0'
        elif tag_text == '0-1':
            res = '0.0'
        elif tag_text == '1/2-1/2':
            res = '0.5'

    return res


def get_sourceid(game_text, tag):
    tag_text = game_text.headers.get(tag)
    site_arr = []
    site, site_id = '', ''

    if tag_text is not None:
        if tag_text.find('lichess', 0) >= 0:
            site = 'Lichess'
            site_id = tag_text.split('/')[-1]
        elif tag_text.find('Chess.com', 0) >= 0:
            site = 'Chess.com'
            lnk = game_text.headers.get('Link')
            if lnk is not None:
                site_id = lnk.split('/')[-1]
        elif tag_text.find('FICS', 0) >= 0:
            site = 'FICS'
            site_id = game_text.headers.get('FICSGamesDBGameNo')

    site_arr.append(site)
    site_arr.append(site_id)
    return site_arr


def get_tag(game_text, tag):
    tag_text = game_text.headers.get(tag)
    if not tag_text:
        tag_text = ''
    return tag_text
