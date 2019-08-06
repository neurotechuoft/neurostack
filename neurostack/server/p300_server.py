from sanic import Sanic
import socketio
import ml

import numpy as np
from sklearn.model_selection import train_test_split

# for testing
import random

# for database
from sqlalchemy import create_engine, text
import os
import hashlib
import binascii


def hash_password(password):
    """Hash a password for storing."""
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


class P300Service:
    def __init__(self):
        self.sio = socketio.AsyncServer(async_mode='sanic')
        self.app = Sanic()
        self.sio.attach(self.app)

        self.clf = {}
        self.inputs = {}
        self.targets = {}

        self.last_uuid = {}
        self.last_acc = {}

        self.users = {}

    def update_weights(self, uuid, accuracy, weights_path):
        engine = create_engine(os.environ['DATABASE_URL'])
        with engine.begin() as connection:

            if uuid:
                # Check whether there is a uuid in the database that matches the one given
                uuid_exists = connection.execute(
                    text('''
                        SELECT
                            w.id
                        FROM user_weights w
                        WHERE w.uuid = :uuid
                    '''),
                    uuid=uuid
                ).fetchall()

                # Update weights for uuid
                if uuid_exists:
                    connection.execute(
                        text('''
                            UPDATE user_weights
                            SET
                                accuracy = :accuracy,
                                weights = :weights,
                                last_updated = NOW()::TIMESTAMP
                            WHERE
                                uuid = :uuid
                        '''),
                        uuid=uuid,
                        accuracy=accuracy,
                        weights=weights_path
                    )
                    return True

                # Create new entry in database with uuid
                else:
                    connection.execute(
                        text('''
                            INSERT INTO user_weights ("uuid", "accuracy", "weights", "last_updated")
                            VALUES (
                                :uuid,
                                :accuracy,
                                :weights,
                                NOW()::TIMESTAMP
                            )
                        '''),
                        uuid=uuid,
                        accuracy=accuracy,
                        weights=weights_path
                    )
                    return True

            # Something went wrongx
            return False

    async def load_classifier(self, uuid, args):
        try:
            self.clf[uuid] = ml.load(self.users[uuid]["weights"])
            return uuid, True
        except FileNotFoundError:
            raise Exception(f'Cannot load classifier')

    async def train_classifier(self, uuid, args):
        eeg_data, p300 = args

        # initialize if empty
        self.inputs[uuid] = self.inputs.get(uuid, [])
        self.targets[uuid] = self.targets.get(uuid, [])

        self.inputs[uuid].append(np.array(eeg_data))
        self.targets[uuid].append(np.array(p300))

        if len(self.targets[uuid]) % 10 == 0 and len(self.targets[uuid]) >= 20:
            X = np.array(self.inputs[uuid])
            y = np.array(self.targets[uuid])

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

            # Note in Barachant's ipynb, 'erpcov_mdm' performed best. 'vect_lr' is the
            # universal one for EEG data.

            # train
            self.clf[uuid] = ml.ml_classifier(X_train, y_train, classifier=None, pipeline='vect_lr')
            acc = self.clf[uuid].score(X_test, y_test)

            # save classifier
            if not os.path.exists('clfs'):
                os.makedirs('clfs')
            ml.save(f'clfs/{self.users[uuid]["username"]}', self.clf[uuid])

            self.update_weights(uuid=uuid, accuracy=acc, weights_path=f'clfs/{self.users[uuid]["username"]}')

            results = (uuid, acc)
            return uuid, results
        return uuid, None

    async def retrieve_prediction_results(self, uuid, args):
        uuid, data = args
        data = np.array(data)
        data = np.expand_dims(data, axis=0)

        # load classifier if not already loaded
        load_classifier()
        p300 = self.clf[uuid].predict(data)[0]

        score = 1
        results = (uuid, p300, score)
        return uuid, results

    # for testing
    async def retrieve_prediction_results_test(self, uuid, args):
        results = {
            'uuid': args['uuid'],
            'p300': random.choice([True, False]),
            'score': random.random()
        }
        return results

    async def train_classifier_test(self, uuid, args):
        results = {
            'uuid': args['uuid'],
            'acc': random.random()
        }
        return results

    def initialize_handlers(self):
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
