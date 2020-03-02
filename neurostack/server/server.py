import binascii
import hashlib
import json
import os
import random
import socketio
from sanic import Sanic

from utils import generate_uuid
from server.services.left_right import LeftRightService
from server.services.p300 import P300Service


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


class NeurostackServer:
    def __init__(self):
        self.sio = socketio.AsyncServer(async_mode='sanic')
        self.app = Sanic()
        self.sio.attach(self.app)

        self.services = {}

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
        # initialize service if it does not exist already
        if self.services.get('left_right') is None:
            self.services['left_right'] = LeftRightService()

        # load arguments, generate UUID if none is provided
        uuid = args['uuid'] if args['uuid'] != 'None' else generate_uuid()
        data = args['data']
        left = args['left']

        results = self.services['left_right'].train(uuid=uuid, data=data, left=left)
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
        # initialize service if it does not exist already
        if self.services.get('left_right') is None:
            self.services['left_right'] = LeftRightService()

        # load arguments, generate UUID if none is provided
        uuid = args['uuid'] if args['uuid'] != 'None' else generate_uuid()
        data = args['data']

        results = self.services['left_right'].predict(uuid=uuid, data=data)
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
        # initialize service if it does not exist already
        if self.services.get('p300') is None:
            self.services['p300'] = P300Service()

        # load arguments, generate UUID if none is provided
        uuid = args['uuid'] if args['uuid'] != 'None' else generate_uuid()
        data = args['data']
        p300 = args['p300']

        results = self.services['p300'].train(uuid=uuid, data=data, p300=p300)
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
        # initialize service if it does not exist already
        if self.services.get('p300') is None:
            self.services['p300'] = P300Service()

        # load arguments, generate UUID if none is provided
        uuid = args['uuid'] if args['uuid'] != 'None' else generate_uuid()
        data = args['data']

        results = self.services['p300'].predict(uuid=uuid, data=data)
        return results

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
