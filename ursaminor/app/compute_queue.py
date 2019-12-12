import os
import numpy as np
import pandas as pd
import loompy
from werkzeug import secure_filename
from multiprocessing import Process
import northstar


class NorthstarRun():
    def __init__(self, method='average', **kwargs):
        self.method = method
        self.kwargs = kwargs

    def compute_files(self, jobid=None):
        while jobid is None:
            jobid = np.random.randint(10000000)
            logfile = 'data/logs/log_{:}.txt'.format(jobid)
            if os.path.isfile(logfile):
                jobid = None
        self.logfile = 'data/logs/log_{:}.txt'.format(jobid)
        self.outfile = 'data/results/results_{:}.txt'.format(jobid)
        self.jobid = jobid

    def save_input_matrix(self, field):
        fn = secure_filename(field.filename)
        fn_ext = fn.split('.')[-1]
        if fn_ext == 'tsv':
            fn = 'data/input/input_{:}.tsv'.format(self.jobid)
            field.save(fn)
            self.newdata = pd.read_csv(fn, sep='\t', index_col=0)
        elif fn_ext == 'loom':
            fn = 'data/input/input_{:}.loom'.format(self.jobid)
            field.save(fn)
            with loompy.connect(fn) as dsl:
                # FIXME: let the user specify as expandable form fields
                genes = dsl.ra[dsl.ra.keys()[0]]
                cells = dsl.ca[dsl.ca.keys()[0]]
                self.newdata = pd.DataFrame(
                    data=dsl[:, :],
                    index=genes,
                    columns=cells,
                    )
        else:
            raise ValueError('File format not supported: {:}'.format(fn_ext))
        os.remove(fn)

    def fit(self):
        global p
        p = Process(
            target=self.computeNorthstar,
            args=(self.logfile, self.outfile, self.method, self.newdata),
            kwargs=self.kwargs,
            )
        p.start()

    @staticmethod
    def computeNorthstar(logfile, outfile, method, new_data, **kwargs):
        if method == 'average':
            model = northstar.Averages(
                **kwargs,
                )
        else:
            model = northstar.Subsample(
                **kwargs,
                )

        model.fit(new_data)
        membership = model.membership

        with open(outfile, 'w') as f:
            f.write('\n'.join(membership))

        with open(logfile, 'w') as f:
            f.write('Done')
