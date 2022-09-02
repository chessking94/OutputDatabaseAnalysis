import json
import os

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

def get_conf(key):
    fpath = r'C:\Users\eehunt\Repository'
    fname = 'confidential.json'
    with open(os.path.join(fpath, fname), 'r') as t:
        key_data = json.load(t)
    val = key_data.get(key)
    return val

def get_config(filepath, key):
    filename = os.path.join(filepath, 'config.json')
    with open(filename, 'r') as t:
        key_data = json.load(t)
    val = key_data.get(key)
    return val

def piececount(fen):
    end = fen.find(' ', 1)
    brd = fen[0:end]
    ct = 0
    for x in brd:
        if x.isalpha():
            ct = ct + 1
    return ct
