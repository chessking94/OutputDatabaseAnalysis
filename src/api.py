import json
import logging
import math
import os
import time

from automation import misc
import requests

from constants import CONFIG_FILE


def bookmoves(fen, date):
    token_value = os.getenv('LichessAPIToken')

    base_url = 'https://explorer.lichess.ovh/lichess?variant=standard&speeds=rapid,classical,correspondence&ratings=2000,2200,2500&fen='
    url = base_url + fen.replace(' ', '_')
    if date is not None:  # this check is in place to essentially avoid my own Lichess games from being referenced in the explorer API
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

            if ct == 5:  # exit ability to avoid infinite loop
                logging.info('API rejected 5 consecutive times, skipping!')
                cde = 200

    return theory


def tbsearch(fen):
    token_value = misc.get_config('lichessAPIToken', CONFIG_FILE)

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
                            m = m + 1
                            if fen.find('w', 0) >= 0:
                                m = m * (-1)
                            m = math.ceil(m/2)
                        else:
                            if tb_results['moves'][j]['checkmate']:
                                if fen.find('w', 0) >= 0:
                                    m = 1
                                else:
                                    m = -1
                        m = str(m)
                    tbmove.append(m)

                    # dtz
                    z = tb_results['moves'][j]['dtz']
                    if z is not None:
                        if z < 0:  # winning
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
                            if tb_results['moves'][j]['checkmate']:
                                if fen.find('w', 0) >= 0:
                                    z = 1
                                else:
                                    z = -1
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

            if ct == 5:  # exit ability to avoid infinite loop
                logging.info('API rejected 5 consecutive times, skipping!')
                cde = 200

    return info
