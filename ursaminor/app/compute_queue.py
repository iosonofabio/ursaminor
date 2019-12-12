import os
import northstar



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

