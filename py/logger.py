class Logger:
    __instance = None

    @staticmethod
    def get_instance(log=True):
        if Logger.__instance is None:
            Logger(log)
        else:
            Logger.__instance.log = log

        return Logger.__instance

    def __init__(self, log=True):
        if self.__instance is None:
            self.log = log
            Logger.__instance = self

    def print(self, text):
        if self.log:
            print(text)

LOG = Logger.get_instance().print