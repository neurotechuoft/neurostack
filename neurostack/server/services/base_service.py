import os
from abc import ABC, abstractmethod

import numpy as np

import server.ml as ml


class BaseService(ABC):

    def __init__(self):
        """
        Initialize fields that all services should have
        """
        self.clf = {}       # classifiers with UUID as key
        self.inputs = {}    # training data with UUID as key
        self.targets = {}

    @abstractmethod
    def train(self, *args):
        """
        Method to make a prediction with a given classifier

        :param args: Arguments from the client, containing data and targets
                     to train on.
        :return: Results of training / accuracy score
        """
        pass

    @abstractmethod
    def predict(self, *args):
        """
        Method to make a prediction with a given classifier

        :param args: Arguments from the client, containing data to make
                     predictions on.
        :return: Results of prediction
        """
        pass

    #
    #   Helper methods
    #

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

    def save_inputs(self, uuid, data, labels):
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
