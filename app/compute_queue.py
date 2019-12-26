import os
import numpy as np
import pandas as pd
import loompy
from werkzeug import secure_filename
from multiprocessing import Process
import northstar

root_fdn = '/home/ubuntu/ursaminor/'


class NorthstarRun():
    def __init__(self, method='average', **kwargs):
        self.method = method
        self.kwargs = kwargs

    def compute_files(self, jobid=None):
        while jobid is None:
            jobid = np.random.randint(10000000)
            logfile = root_fdn+'data/logs/log_{:}.txt'.format(jobid)
            if os.path.isfile(logfile):
                jobid = None
        self.logfile = root_fdn+'data/logs/log_{:}.txt'.format(jobid)
        self.outfile = root_fdn+'data/results/results_{:}.tsv'.format(jobid)
        self.jobid = jobid

    def save_input_matrix(self, field):
        fn = secure_filename(field.filename)
        fn_ext = fn.split('.')[-1]
        if fn_ext == 'tsv':
            fn = root_fdn+'data/input/input_{:}.tsv'.format(self.jobid)
            field.save(fn)
            self.newdata = pd.read_csv(fn, sep='\t', index_col=0).astype(np.float32)
        elif fn_ext == 'csv':
            fn = root_fdn+'data/input/input_{:}.csv'.format(self.jobid)
            field.save(fn)
            self.newdata = pd.read_csv(fn, sep=',', index_col=0).astype(np.float32)   
        elif fn_ext == 'loom':
            fn = root_fdn+'data/input/input_{:}.loom'.format(self.jobid)
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
            # FIXME: do better than this!
            if 'n_neighbors_out_of_atlas' in kwargs:
                del kwargs['n_neighbors_out_of_atlas']
            if 'n_cells_per_type' in kwargs:
                del kwargs['n_cells_per_type']
            model = northstar.Subsample(
                **kwargs,
                )

        model.fit(new_data)
        membership = model.membership

        with open(outfile, 'w') as f:
            f.write('CellID\tCell type\n')
            for i in range(len(membership)):
                f.write('{:}\t{:}\n'.format(new_data.columns[i], membership[i]))

        with open(logfile, 'w') as f:
            f.write('Done')
