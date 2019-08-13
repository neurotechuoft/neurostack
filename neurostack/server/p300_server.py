from sanic import Sanic
import socketio
import ml
import numpy as np
from sklearn.model_selection import train_test_split
import uuid

# for testing
import random

# for database
from sqlalchemy import create_engine, text
import os
import hashlib
import binascii


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


def generate_uuid():
    """Generates a universally unique ID"""
    # Completely random UUID; use uuid1() for a UUID based on host MAC address
    # and current time
    return str(uuid.uuid4())


class P300Service:
    def __init__(self):
        self.sio = socketio.AsyncServer(async_mode='sanic')
        self.app = Sanic()
        self.sio.attach(self.app)

        self.clf = {}       # classifiers with UUID as key
        self.inputs = {}    # training data with UUID as key
        self.targets = {}

    async def save_classifier(self, uuid):
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

    async def load_classifier(self, uuid):
        """
        Load classifier for client with given UUID into self.clf

        :param uuid: client UUID
        :returns: True if classifier is successfully loaded, else False
        """
        try:
            if self.clf[uuid] is None:
                self.clf[uuid] = ml.load(f'clfs/{uuid}')
            return True
        except FileNotFoundError:
            print(f'Cannot load classifier')
            return False

    async def train_classifier(self, sid, args):
        """
        Endpoint for training classifier--given enough data, will train
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
        uuid = args.get(['uuid'], generate_uuid())
        eeg_data = args['data']
        p300 = args['p300']

        # initialize if empty
        self.inputs[uuid] = self.inputs.get(uuid, [])
        self.targets[uuid] = self.targets.get(uuid, [])

        self.inputs[uuid].append(np.array(data))
        self.targets[uuid].append(np.array(p300))

        if len(self.targets[uuid]) % 10 == 0 and len(self.targets[uuid]) >= 30:
            X = np.array(self.inputs[uuid])
            y = np.array(self.targets[uuid])

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

            # Note in Barachant's ipynb, 'erpcov_mdm' performed best. 'vect_lr' is the
            # universal one for EEG data.

            # train
            self.clf[uuid] = ml.ml_classifier(X_train, y_train, classifier=None, pipeline='vect_lr')
            acc = self.clf[uuid].score(X_test, y_test)

            save_classifier(uuid)

            results = {
                'uuid': args['uuid'],
                'acc': acc
            }
            return results

        return None

    async def retrieve_prediction_results(self, sid, args):
        """
        Endpoint for making predictions with trained classifier

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
        uuid = args.get(['uuid'], generate_uuid())
        data = args['data']

        # prepare data for prediction
        data = np.array(data)
        data = np.expand_dims(data, axis=0)

        # load classifier if not already loaded
        if load_classifier(uuid)
            p300 = self.clf[uuid].predict(data)[0]
        else:
            raise Exception('Cannot load classifier and make prediction')

        # currently we do not have a confidence method
        score = 1

        results = {
            'uuid': uuid,
            'p300': p300,
            'score': random.random()
        }
        return results

    #
    # For testing
    #

    async def retrieve_prediction_results_test(self, sid, args):
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
        uuid = args.get(['uuid'], generate_uuid())
        results = {
            'uuid': uuid,
            'p300': random.choice([True, False]),
            'score': random.random()
        }
        return results

    async def train_classifier_test(self, sid, args):
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
        uuid = args.get(['uuid'], generate_uuid())
        results = {
            'uuid': uuid,
            'acc': random.random()
        }
        return results

    def initialize_handlers(self):
        """Initialize handlers for server"""
        # train classifier and predict
        self.sio.on("retrieve_prediction_results", self.retrieve_prediction_results)
        self.sio.on("train_classifier", self.train_classifier)
        self.sio.on("load_classifier", self.load_classifier)

        # for testing
        self.sio.on("retrieve_prediction_results_test", self.retrieve_prediction_results_test)
        self.sio.on("train_classifier_test", self.train_classifier_test)


if __name__ == '__main__':
    service = P300Service()
    service.initialize_handlers()

    service.app.run(host='localhost', port=8001)
