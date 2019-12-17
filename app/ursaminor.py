import os
import time
import pandas as pd

from flask import Flask, escape, request, render_template, send_from_directory

from compute_queue import NorthstarRun
from form import NorthstarForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'the-one-up-in-the-sky'

# Remove all temp files
def remove_files():
    for fdn in ['logs', 'results']:
        for fn in os.listdir('data/{:}'.format(fdn)):
            os.remove('data/{:}/{:}'.format(fdn, fn))
remove_files()


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NorthstarForm()
    form.get_atlas_choices()

    if form.validate_on_submit():

        model_wrap = NorthstarRun(
            method=form.method.data,
            atlas=form.atlas.data,
            n_features_per_cell_type=form.nfeact.data,
            n_features_overdispersed=form.nfeaod.data,
            n_pcs=form.npcs.data,
            n_neighbors=form.nnei.data,
            n_neighbors_out_of_atlas=form.nneia.data,
            n_cells_per_type=20,
            distance_metric='correlation',
            threshold_neighborhood=0.8,
            clustering_metric='cpm',
            resolution_parameter=form.respar.data,
            )
        model_wrap.compute_files()
        model_wrap.save_input_matrix(request.files['fileupload'])
        model_wrap.fit()

        # Format jobID for queries
        jobid = model_wrap.jobid
        endpoint = '/progress/{0}'.format(jobid)

        return render_template('progress.html', jobid=jobid, endpoint=endpoint)

    else:
        if form.errors:
            for field, errors in form.errors.items():
                if field == 'fileupload':
                    return errors[0]
                return ', '.join(errors)
        else:
            return render_template('index.html', form=form)


@app.route('/progress/<path>')
def progress(path):
    model_wrap = NorthstarRun()
    model_wrap.compute_files(path)
    if os.path.isfile(model_wrap.logfile):
        with open(model_wrap.logfile, 'rt') as f:
            log = f.read()
        if 'Done' in log:
            response = '<div class="linkToDownload"><a href="/results/{:}">Download</a></div>'.format(
                os.path.basename(model_wrap.outfile))

            with open(model_wrap.outfile, 'rt') as f:
                response += '<div class="resultsList">'
                for line in f:
                    cellID, cellType = line.rstrip('\n').split('\t')
                    response += '{:} {:}<br>'.format(cellID, cellType)
                response += '</div>'

            os.remove(model_wrap.logfile)
            #os.remove(model_wrap.outfile)

            return response
    else:
        response = ''
        return response


@app.route('/results/<path>')
def result(path):
    return send_from_directory(
        '../data/results',
        path,
        as_attachment=True,
        mimetype='text/tab-separated-values',
        attachment_filename='northstar_result.tsv',
        )