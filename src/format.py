import logging
import math

import chess.engine


def get_tournament(game_text, tag):
    tag_text = game_text.headers.get(tag)
    tmnt_len = 50
    tmnt = ''.ljust(tmnt_len, ' ')

    if tag_text is not None:
        tmnt = tag_text.ljust(tmnt_len, ' ')

    return tmnt


def get_name(game_text, tag):
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


def get_elo(game_text, tag):
    tag_text = game_text.headers.get(tag)
    elo_len = 4
    elo = ''.ljust(elo_len, ' ')

    if tag_text is not None:
        elo = tag_text.ljust(elo_len, ' ')

    return elo


def get_date(game_text, tag):
    tag_text = game_text.headers.get(tag)
    dte_arr = []
    dte_len = 10
    dte = ''.ljust(dte_len, ' ')
    dte_val = None

    if tag_text is not None:
        dte = tag_text.ljust(dte_len, ' ')
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


def get_round(game_text, tag):
    tag_text = game_text.headers.get(tag)
    rd_len = 7
    rd = '?'.ljust(rd_len, ' ')

    if tag_text is not None:
        rd = tag_text.ljust(rd_len, ' ')
        rd = rd.replace('-', '?')

    return rd


def get_eco(game_text, tag):
    tag_text = game_text.headers.get(tag)
    eco_len = 3
    eco = ''.ljust(eco_len, ' ')

    if tag_text is not None:
        eco = tag_text.ljust(eco_len, ' ')

    return eco


def get_result(game_text, tag):
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


def get_moves(game_text, tag):
    tag_text = game_text.headers.get(tag)
    mv_len = 3
    mv = ''.ljust(mv_len, ' ')

    if tag_text is not None:
        mv = str(math.ceil(int(tag_text)/2)).ljust(mv_len, ' ')

    return mv


def get_sourceid(game_text, tag):
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


def get_timecontrol(game_text, tag):
    tag_text = game_text.headers.get(tag)
    tc_len = 15
    tc = ''.ljust(tc_len, ' ')

    if tag_text is not None:
        tc = tag_text.ljust(tc_len, ' ')

    return tc


def get_pgneval(eval):
    ev = ''
    if eval is not None:
        if chess.engine.Score.is_mate(eval):
            ev = str(eval)
        else:
            ev = str(round(int(eval.score())/100., 2))

    return ev
