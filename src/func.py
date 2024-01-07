def tbeval(tbdata):
    # returns #-n, #+n, #+nZ, and #-nZ
    if tbdata[1] is not None:  # DTM populated, takes priority
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


def piececount(fen):
    end = fen.find(' ', 1)
    brd = fen[0:end]
    ct = 0
    for x in brd:
        if x.isalpha():
            ct = ct + 1
    return ct
