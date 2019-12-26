import os
import numpy as np
import pandas as pd
import loompy
from werkzeug import secure_filename
from multiprocessing import Process
import northstar

import matplotlib.pyplot as plt
import seaborn as sns


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
        self.outfile = 'data/results/results_{:}.tsv'.format(jobid)
        self.embedimgfile = 'data/results/results_{:}_embedding.png'.format(jobid)
        self.jobid = jobid

    def save_input_matrix(self, field):
        fn = secure_filename(field.filename)
        fn_ext = fn.split('.')[-1]
        if fn_ext == 'tsv':
            fn = 'data/input/input_{:}.tsv'.format(self.jobid)
            field.save(fn)
            self.newdata = pd.read_csv(fn, sep='\t', index_col=0).astype(np.float32)
        elif fn_ext == 'csv':
            fn = 'data/input/input_{:}.csv'.format(self.jobid)
            field.save(fn)
            self.newdata = pd.read_csv(fn, sep=',', index_col=0).astype(np.float32)
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
            args=(self.logfile, self.outfile, self.embedimgfile, self.method, self.newdata),
            kwargs=self.kwargs,
            )
        p.start()

    @staticmethod
    def computeNorthstar(
            logfile,
            outfile,
            imgfile,
            method,
            new_data,
            **kwargs,
            ):
        def sanitize_kwargs(method, kwargs):
            if method != 'average':
                # FIXME: do better than this
                if 'n_neighbors_out_of_atlas' in kwargs:
                    del kwargs['n_neighbors_out_of_atlas']
                if 'n_cells_per_type' in kwargs:
                    del kwargs['n_cells_per_type']

        def plot_embedding(vs, imgfile):
            x, y, ct = vs.values.T
            ctu = np.unique(ct)
            colors = sns.color_palette('husl', len(ctu))

            height = 4 + 0.3 * len(ctu)
            fig, ax = plt.subplots(1, 1, figsize=(4, height))
            for i, cti in enumerate(ctu):
                ind = ct == cti
                ax.scatter(
                    x[ind], y[ind],
                    s=20,
                    color=colors[i],
                    alpha=0.5,
                    label=cti
                    )
                #xm = x[ind].mean()
                #ym = y[ind].mean()
                #ax.text(xm, ym, cti, ha='center', va='center')
            ax.legend(
                loc='upper left',
                bbox_to_anchor=(0, -0.02),
                bbox_transform=ax.transAxes,
                title='Legend:',
                )
            ax.set_axis_off()
            fig.tight_layout()
            fig.savefig(imgfile)
            plt.close(fig)

        embedding = kwargs.pop('embedding', 'tsne')
        sanitize_kwargs(method, kwargs)

        if method == 'average':
            model = northstar.Averages(
                **kwargs,
                )
        else:
            model = northstar.Subsample(
                **kwargs,
                )

        with open(logfile, 'w') as f:
            f.write('Northstar model ready.\n')
            f.write('Computing cell types...')

        model.fit(new_data)
        membership = model.membership

        with open(logfile, 'a') as f:
            f.write(' Cell types computed.\n')
            f.write('Calculating embedding...')

        # Compute embedding with atlas and newdata, but only show newdata
        if embedding == 'tsne':
            vs = model.embed(
                method=embedding,
                perplexity=30,
                )
            vs = vs.loc[model.cell_names_newdata]
        elif embedding in ('pca', 'umap'):
            vs = model.embed(
                method=embedding,
                )
            vs = vs.loc[model.cell_names_newdata]
        else:
            raise ValueError('Embedding {:} not supported'.format(embedding))

        with open(logfile, 'a') as f:
            f.write(' Embedding computed.\n')
            f.write('Plotting embedding...')

        vs['Cell type'] = membership
        plot_embedding(vs, imgfile)

        with open(logfile, 'a') as f:
            f.write(' Embedding plotted.\n')
            f.write('Writing output file...')

        with open(outfile, 'w') as f:
            f.write('CellID\tCell type\tDimension 1\tDimension 2\n')
            for i in range(len(membership)):
                f.write('{:}\t{:}\t{:}\t{:}\n'.format(
                    new_data.columns[i], membership[i],
                    vs.values[i, 0], vs.values[i, 1]))

        with open(logfile, 'a') as f:
            f.write('Done')
