from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug import secure_filename
from wtforms import SelectField, RadioField, SubmitField, IntegerField, FloatField, validators, ValidationError

from atlas_landmarks import get_atlases


class NorthstarForm(FlaskForm):
    fileupload = FileField('New data (TSV)')
    submit = SubmitField('northstar!')
    atlas = SelectField('Atlas')
    method = RadioField('Method', choices=[('average', 'average'), ('subsample', 'subsample (20)')], default='average')
    embedding = RadioField('Embedding', choices=[('tsne', 't-SNE'), ('umap', 'UMAP'), ('pca', 'PCA')], default='tsne')
    nfeact = IntegerField('nfeact', default=30)
    nfeaod = IntegerField('nfeaod', default=20)
    npcs = IntegerField('npcs', default=25)
    nnei = IntegerField('nnei', default=15)
    nneia = IntegerField('nneia', default=5)
    respar = FloatField('respar', default=0.001)

    def get_atlas_choices(self):
        self.atlas.choices = [(x, x) for x in get_atlases()]

    def validate_fileupload(form, field):
        if field.data is None:
            raise ValidationError('No file uploaded')
        fn = secure_filename(field.data.filename)
        fn_ext = fn.split('.')[-1]

        formats_supported = ('tsv', 'csv', 'loom')
        if fn_ext not in formats_supported:
            raise ValidationError(
                'Uploaded file format not supported. Supported formats: {:}'.format(', '.join(formats_supported)))
        return True

    def validate_nfeact(form, field):
        if field.data < 0:
            raise ValidationError('Number of features per cell type must be zero or more')

    def validate_nfeaod(form, field):
        if field.data < 0:
            raise ValidationError('Number of overdispersed features must be zero or more')

    def validate_npcs(form, field):
        if field.data < 2:
            raise ValidationError('Number of PCs must be >= 2')
        return True

    def validate_nnei(form, field):
        if field.data < 1:
            raise ValidationError('Number of graph neighbors must be >= 1')
        return True

    def validate_nneia(form, field):
        if field.data < 1:
            raise ValidationError('Number of graph neighbors out of atlas must be >= 1')
        return True

    def vaidate_respar(form, field):
        if (field.data > 1) or (field.data <= 0):
            raise ValidationError('Resolution parameter must be between 0 (excluded) and 1 (included). Typical values are around 0.001')

