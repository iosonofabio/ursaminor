import os
import time
from multiprocessing import Process
import numpy as np
import pandas as pd

from flask import Flask, escape, request, render_template
from werkzeug import secure_filename
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SelectField, SubmitField, validators, ValidationError

from atlas_landmarks import get_atlases
from compute_queue import computeNorthstar


app = Flask(__name__)
app.config['SECRET_KEY'] = 'the-one-up-in-the-sky'

# Remove all temp files
def remove_files():
    for fdn in ['logs', 'results']:
        for fn in os.listdir('data/{:}'.format(fdn)):
            os.remove('data/{:}/{:}'.format(fdn, fn))
remove_files()


class NorthstarRun():
    def __init__(self, method='average', **kwargs):
        self.method = method
        self.kwargs = kwargs

    def compute_files(self, jobid=None):
        if jobid is None:
            jobid = np.random.randint(10000000)
        self.logfile = 'data/logs/log_{:}.txt'.format(jobid)
        self.outfile = 'data/results/log_{:}.txt'.format(jobid)
        self.jobid = jobid

    def fit(self, new_data):
        global p
        p = Process(
            target=computeNorthstar,
            args=(self.logfile, self.outfile, self.method, new_data),
            kwargs=self.kwargs,
            )
        p.start()


class NorthstarForm(FlaskForm):
    submit = SubmitField('northstar!')
    atlas = SelectField('Atlas')
    fileupload = FileField('New data (TSV)')

    def get_atlas_choices(self):
        self.atlas.choices = [(x, x) for x in get_atlases()]

    def validate_fileupload(form, field):
        fn = secure_filename(field.data.filename)
        fn_ext = fn.split('.')[-1]
        if fn_ext != 'tsv':
            raise ValidationError('Uploaded file was not TSV')
        return True


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
        res = model_wrap.jobid
        res_string = 'JOB ID: {0}</br>PROGRESS ENDPOINT: /progress/{0}'.format(res)

        return res_string

    else:
        if form.errors:
            for field, errors in form.errors.items():
                if field == 'fileupload':
                    return errors[0]
                #print(form.atlas.data)
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
                response = '</br>'.join(f.read().split('\n'))

            os.remove(model_wrap.logfile)
            os.remove(model_wrap.outfile)

            return response

    else:
        response = 'In progress'
        return response
