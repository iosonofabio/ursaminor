import os
import numpy as np
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
        self.outfile = 'data/results/log_{:}.txt'.format(jobid)
        self.jobid = jobid

    def fit(self, new_data):
        global p
        p = Process(
            target=self.computeNorthstar,
            args=(self.logfile, self.outfile, self.method, new_data),
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
