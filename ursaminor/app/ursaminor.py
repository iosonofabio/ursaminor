import os
import time
import pandas as pd

from flask import Flask, escape, request, render_template

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

        # Read in data via file
        f = request.files['fileupload']
        fn = 'data/input/new_data.tsv'
        f.save(fn)
        try:
            newdata = pd.read_csv(fn, sep='\t', index_col=0)
        finally:
            os.remove(fn)

        model_wrap = NorthstarRun(
            method='average',
            atlas=form.atlas.data,
            n_features_overdispersed=20,
            )
        model_wrap.compute_files()
        model_wrap.fit(newdata)

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
            with open(model_wrap.outfile, 'rt') as f:
                response = '<br>'.join(f.read().split('\n'))

            os.remove(model_wrap.logfile)
            os.remove(model_wrap.outfile)

            print(response)
            return response
    else:
        response = 'In progress'
        return response
