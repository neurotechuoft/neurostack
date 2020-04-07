import numpy as np
from mne.decoding import CSP
from scipy import stats
from scipy.signal import filtfilt, iirdesign
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.svm import SVC


# output is of shape (n_epochs,n_filters*n_csp_component) because we have "n_filters" different frequency bands
# and for each we have n_csp_component values in the array
def create_fbcsp(low_freq, n_filters=12, band_overlap=2,
                 band_width=4, n_csp_components=2, n_jobs=1):
    pipeline_list = []
    step = band_width - band_overlap
    bands = range(low_freq, low_freq + n_filters * step, step)
    for low in bands:
        pipeline_list.append(
            ("pipe%d" % low, Pipeline([
                ("filter", BandPassFilter(low, low + band_width)),
                ("csp", CSP(n_components=n_csp_components))
            ]))
        )

    return FeatureUnion(pipeline_list, n_jobs=n_jobs)


class BandPassFilter(BaseEstimator, TransformerMixin):

    def __init__(self, low_freq=7., high_freq=30., gpass=0.5, gstop=10.,
                 sfreq=250., ftype='cheby2'):
        nyquist = sfreq / 2.
        wp = [low_freq / nyquist, high_freq / nyquist]
        ws = [(low_freq - 0.5) / nyquist, (high_freq + 0.5) / nyquist]
        self.b, self.a = iirdesign(wp, ws, gpass, gstop, ftype=ftype)

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return filtfilt(self.b, self.a, X)
