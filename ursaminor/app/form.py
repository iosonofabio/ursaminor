from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug import secure_filename
from wtforms import SelectField, SubmitField, validators, ValidationError

from atlas_landmarks import get_atlases


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
