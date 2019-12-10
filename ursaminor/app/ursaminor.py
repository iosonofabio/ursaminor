import pandas as pd
import northstar

import requests
from flask import Flask, escape, request, render_template
from werkzeug import secure_filename
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SelectField, SubmitField, validators, ValidationError


app = Flask(__name__)

app.config['SECRET_KEY'] = 'the-one-up-in-the-sky'


#FIXME: this can be outsourced to an external queue manager
class NorthstarRun():
    def __init__(self, method, **kwargs):
        self.kwargs = kwargs
        if method == 'average':
            self.model = northstar.Averages(
                **self.kwargs,
                )
        else:
            self.model = northstar.Subsample(
                **self.kwargs,
                )

    def fit(self, new_data):
        self.model.fit(new_data)
        self.membership = self.model.membership


def get_atlases():
    url = 'https://raw.githubusercontent.com/northstaratlas/atlas_landmarks/master/table.tsv'
    response = requests.get(url)
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
        # Save tsv file to file
        f = request.files['fileupload']
        fn = 'data/new_data.tsv'
        f.save(fn)

        # Prepare northstar
        model_wrap = NorthstarRun(
            method='average',
            atlas=form.atlas.data,
            #FIXME
            n_features_overdispersed=20,
            )

        # Read new data from file
        newdata = pd.read_csv(fn, sep='\t', index_col=0)

        # Classify
        model_wrap.fit(newdata)

        # Format output
        res = model_wrap.membership
        res_string = '</br>'.join(['Cell types:'] + list(res))

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
