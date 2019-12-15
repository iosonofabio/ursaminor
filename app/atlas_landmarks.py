import pandas as pd
import requests


def get_atlases():
    url = 'https://raw.githubusercontent.com/northstaratlas/atlas_landmarks/master/table.tsv'

    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        return pd.read_csv(
            '/home/fabio/university/postdoc/atlas_landmarks/table.tsv',
            sep='\t',
            index_col=0).index

    if response.status_code != 200:
        raise ValueError('Cannot load atlas landmarks TSV table')

    atlases = []
    text = response.text
    for il, line in enumerate(text.split('\n')):
        if il == 0:
            continue
        atlas_name = line.split('\t')[0]
        if atlas_name:
            atlases.append(atlas_name)

    return atlases
