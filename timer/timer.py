
import time

class Timer():

    def __init__(self):
        self.__start = time.time()
        self.__delta = 0
        self.__last = self.__start
        self.run()

    def run(self):
        self.__delta = time.time() - self.__last
        self.__last = time.time()
		
    @property
    def start(self):
        return self.__start
	
    @property
    def last(self):
        return self.__last
		
    @property
    def delta(self):
        return self.__delta
