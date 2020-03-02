import binascii
import hashlib
import json
import numpy as np
import os
import random
import socketio
from sanic import Sanic
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from mne.decoding import CSP
from scipy.signal import filtfilt, iirdesign
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, FeatureUnion

from server import ml
from utils import generate_uuid


def hash_password(password):
    """Hash a password for storing"""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


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


class NeurostackServer:
    def __init__(self):
        self.sio = socketio.AsyncServer(async_mode='sanic')
        self.app = Sanic()
        self.sio.attach(self.app)

        self.clf = {}       # classifiers with UUID as key
        self.inputs = {}    # training data with UUID as key
        self.targets = {}

    def save_classifier(self, uuid):
        """
        Load classifier for client with given UUID into self.clf

        :param uuid: client UUID
        :returns: True if classifier is successfully loaded, else False
        """
        if not os.path.exists('clfs'):
            os.makedirs('clfs')

        if self.clf[uuid] is not None:
            ml.save(f'clfs/{uuid}', self.clf[uuid])
            return True

        return False

    def load_classifier(self, uuid):
        """
        Load classifier for client with given UUID into self.clf

        :param uuid: client UUID
        :returns: True if classifier is successfully loaded, else False
        """
        try:
            if self.clf.get(uuid) is None:
                self.clf[uuid] = ml.load(f'clfs/{uuid}')
            return True
        except FileNotFoundError:
            print(f'Cannot load classifier')
            return False

    async def left_right_train(self, sid, args):
        """
        Endpoint for training left right classifier

        :param sid: Socket IO session ID, automatically given by connection
        :param args: arguments from client. This should be in the format
                     {
                         'uuid': client UUID
                         'data': EEG data to use for training
                         'left': True or False
                     }
        :returns: None if there is not enough data for training, or the current
                  model accuracy in the format
                  {
                      'uuid': client UUID
                      'acc': current training accuracy
                  }
        """
        # load arguments, generate UUID if none is provided
        uuid = args['uuid'] if args['uuid'] != 'None' else generate_uuid()
        data = args['data']
        left = args['p300']
        self._save_inputs(uuid, data, left)

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
            self.save_classifier(uuid)

            results['acc'] = score

        return results

    async def left_right_predict(self, sid, args):
        """
        Endpoint for making predictions with trained p300 classifier

        :param sid: Socket IO session ID, automatically given by connection
        :param args: arguments from client. This should be in the format
                     {
                         'uuid': client UUID
                         'data': EEG data to make prediction on
                     }
        :returns: prediction results in the format
                  {
                      'uuid': client UUID
                      'left': True or False result of model prediction
                  }
        """
        # load arguments, generate UUID if none is provided
        uuid = args['uuid'] if args['uuid'] != 'None' else generate_uuid()
        data = args['data']

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

    async def p300_train(self, sid, args):
        """
        Endpoint for training p300--given enough data, will train
        classifier

        :param sid: Socket IO session ID, automatically given by connection
        :param args: arguments from client. This should be in the format
                     {
                         'uuid': client UUID
                         'data': EEG data to use for training
                         'p300': True or False
                     }
        :returns: None if there is not enough data for training, or the current
                  model accuracy in the format
                  {
                      'uuid': client UUID
                      'acc': current training accuracy
                  }
        """
        # load arguments, generate UUID if none is provided
        uuid = args['uuid'] if args['uuid'] != 'None' else generate_uuid()
        data = args['data']
        p300 = args['p300']
        self._save_inputs(uuid, data, p300)

        results = {
            'uuid': uuid,
            'acc': None
        }

        if len(self.targets[uuid]) % 10 == 0 and len(self.targets[uuid]) >= 10:
            X = np.array(self.inputs[uuid])
            y = np.array(self.targets[uuid])

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

            # Note in Barachant's ipynb, 'erpcov_mdm' performed best. 'vect_lr' is the
            # universal one for EEG data.

            # train
            self.clf[uuid] = ml.ml_classifier(X_train, y_train, classifier=None, pipeline='vect_lr')
            acc = self.clf[uuid].score(X_test, y_test)

            self.save_classifier(uuid)

            results['acc'] = acc

        return results

    async def p300_predict(self, sid, args):
        """
        Endpoint for making predictions with trained p300 classifier

        :param sid: Socket IO session ID, automatically given by connection
        :param args: arguments from client. This should be in the format
                     {
                         'uuid': client UUID
                         'data': EEG data to make prediction on
                     }
        :returns: prediction results in the format
                  {
                      'uuid': client UUID
                      'p300': True or False result of model P300 prediction
                      'score': confidence value of prediction between 0 and 1
                  }
        """
        # load arguments, generate UUID if none is provided
        uuid = args['uuid'] if args['uuid'] != 'None' else generate_uuid()
        data = args['data']

        # prepare data for prediction
        data = np.array(data)
        data = np.expand_dims(data, axis=0)

        # load classifier if not already loaded
        if self.load_classifier(uuid):
            p300 = self.clf[uuid].predict(data)[0]
        else:
            return 'Cannot load classifier and make prediction'

        # currently we do not have a confidence method
        score = 1

        results = {
            'uuid': uuid,
            'p300': int(p300),
            'score': random.random()
        }
        return results

    #
    # Helper functions
    #

    def _save_inputs(self, uuid, data, labels):
        """
        Save incoming data

        :param uuid: UUID of user sending data
        :param data:
        :param labels:
        :return: None
        """
        # initialize if empty
        self.inputs[uuid] = self.inputs.get(uuid, [])
        self.targets[uuid] = self.targets.get(uuid, [])

        self.inputs[uuid].append(np.array(data))
        self.targets[uuid].append(np.array(labels))

    #
    # For testing
    #

    async def test_predict(self, sid, args):
        """
        Tests endpoint for making predictions with trained classifier

        :param sid: Socket IO session ID, automatically given by connection
        :param args: arguments from client. This should be in the format
                     {
                         'uuid': client UUID
                         'data': EEG data to make prediction on
                     }
        :returns: dummy prediction results, including a True or False for P300
                  and a confidence score
        """
        args = json.loads(args)
        uuid = args.get('uuid', generate_uuid())
        results = {
            'uuid': uuid,
            'p300': random.choice([True, False]),
            'score': random.random()
        }
        return results

    async def test_train(self, sid, args):
        """
        Tests endpoint for training classifier

        :param sid: Socket IO session ID, automatically given by connection
        :param args: arguments from client. This should be in the format
                     {
                         'uuid': client UUID
                         'data': EEG data to use for training
                         'p300': True or False
                     }
        :returns: dummy results of training
        """
        args = json.loads(args)
        uuid = args.get('uuid', generate_uuid())
        results = {
            'uuid': uuid,
            'acc': random.random()
        }
        return results

    def initialize_handlers(self):
        """Initialize handlers for server"""
        # train classifier and predict
        self.sio.on("p300_train", self.p300_train)
        self.sio.on("p300_predict", self.p300_predict)

        self.sio.on("left_right_train", self.left_right_train)
        self.sio.on("left_right_predict", self.left_right_predict)

        # for testing
        self.sio.on("train_test", self.test_train)
        self.sio.on("predict_test", self.test_predict)
