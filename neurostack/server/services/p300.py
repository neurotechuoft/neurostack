import numpy as np
from sklearn.model_selection import train_test_split

import server.ml as ml
from server.services.base_service import BaseService


class P300Service(BaseService):

    def train(self, uuid, data, p300):
        """
        Method to make a prediction with a given classifier

        :param uuid: client UUID
        :param data: EEG data to use for training
        :param p300: True or False
        :returns: None if there is not enough data for training, or the current
                  model accuracy in the format
                  {
                      'uuid': client UUID
                      'acc': current training accuracy
                  }
        """
        self.save_inputs(uuid, data, p300)

        results = {
            'uuid': uuid,
            'timestamp': timestamp,
            'acc': None
        }

        if len(self.targets[uuid]) % 10 == 0 and len(self.targets[uuid]) >= 10:
            X = np.array(self.inputs[uuid])
            y = np.array(self.targets[uuid])

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

            # Note in Barachant's ipynb, 'erpcov_mdm' performed best. 'vect_lr' is the
            # universal one for EEG data.

            # train, score, and save
            clf = ml.ml_classifier(X_train, y_train, classifier=None, pipeline='vect_lr')
            acc = clf.score(X_test, y_test)
            self.save_classifier(uuid, clf)

            results['acc'] = acc

        return results

    def predict(self, uuid, data):
        """
        Method to make a prediction with a given classifier

        :param uuid: client UUID
        :param data: EEG data to make prediction on
        :returns: prediction results in the format
                  {
                      'uuid': client UUID
                      'p300': True or False result of model P300 prediction
                      'score': confidence value of prediction between 0 and 1
                  }
        """
        # prepare data for prediction
        data = np.array(data)
        data = np.expand_dims(data, axis=0)

        # load classifier if not already loaded
        if self.load_classifier(uuid):
            p300 = self.clf[uuid].predict(data)[0]
        else:
            return 'Cannot load classifier and make prediction'

        # TODO: currently we do not have a confidence method
        score = 1
        results = {
            'uuid': uuid,
            'timestamp': timestamp,
            'p300': int(p300),
            'score': score
        }
        return results
