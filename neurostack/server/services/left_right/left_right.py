from server.services.left_right.band_pass_filter import *
from server.services.left_right.feature_selector import *

from server.services.base_service import BaseService


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
