import json
import os

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
