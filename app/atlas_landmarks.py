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
    lines = response.text.split('\n')
    fields = lines[0].split('\t')
    icol_species = fields.index('Species')
    icol_tissue = fields.index('Tissue')
    for line in lines[1:]:
        fields = line.split('\t')
        atlas_name = fields[0]
        if atlas_name:
            species = fields[icol_species]
            tissue = fields[icol_tissue]
            atlases.append({
                'name': atlas_name,
                'species': species,
                'tissue': tissue,
                })

    return atlases
