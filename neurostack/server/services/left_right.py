import numpy as np
from mne.decoding import CSP
from scipy import stats
from scipy.signal import filtfilt, iirdesign
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.svm import SVC

from server.services.base_service import BaseService


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


class FeatureSelector(BaseEstimator, TransformerMixin):

    def __init__(self, features):
        self.features = features

    def fit(self, X, y=None):
        return self

    # Update to automatically select features
    def transform(self, X, y=None):
        return X[:, self.features]


class LeftRightService(BaseService):

    def train(self, uuid, data, left):
        """
        Method to make a prediction with a given classifier

        :param uuid: client UUID
        :param data: EEG data to use for training
        :param left: True or False
        :returns: The current model accuracy in the below format. If there is not
                  enough data, then the 'acc' field will be None (model not trained)
                  {
                      'uuid': client UUID
                      'acc': current training accuracy
                  }
        """
        self.save_inputs(uuid, data, left)

        results = {
            'uuid': uuid,
            'acc': None
        }

        if len(self.targets[uuid]) % 5 == 0 and len(self.targets[uuid]) >= 5:
            # load, normalize, and split data
            X = np.array(self.inputs[uuid])
            X = stats.zscore(X, axis=2)
            y = np.array(self.targets[uuid])

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

            # build model
            fbcsp = create_fbcsp(6, n_jobs=2)
            svc = SVC(kernel="linear")
            clf = Pipeline([
                ("fbcsp", fbcsp),
                ("fselector", FeatureSelector(features=[6, 7])),
                ("classifier", svc)
            ])

            # train, score, and save model
            clf.fit(X_train, y_train)
            score = clf.score(X_test, y_test)
            self.save_classifier(uuid, clf)

            results['acc'] = score

        return results

    def predict(self, uuid, data):
        """
        Method to make a prediction with a given classifier

        :param uuid: client UUID
        :param data: EEG data to make prediction on
        :return: Results of prediction
        """
        # prepare data for prediction
        data = np.array(data)
        data = np.expand_dims(data, axis=0)

        # load classifier if not already loaded
        if self.load_classifier(uuid):
            left = self.clf[uuid].predict(data)[0]
        else:
            return 'Cannot load classifier and make prediction'

        # currently we do not have a confidence method
        results = {
            'uuid': uuid,
            'left': left
        }
        return results
