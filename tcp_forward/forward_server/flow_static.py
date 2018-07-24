import time

class FlowStatic(object):


    def __init__(self):
        self.__init_time = time.time()
        self.__total_flow = 0   #unit:MB
        self.__real_time_speed = 0
        self.__last_add_time = 0

    def add_flow(self,flow):
        self.__total_flow = self.__total_flow + flow
        current_time = time.time()
        if current_time - self.__last_add_time < 3:
            self.__real_time_speed = float(flow)/1024/1024/(current_time - self.__last_add_time)
        else:
            self.__real_time_speed = 0
        self.__last_add_time = current_time

    def get_real_speed(self):
        current_time = time.time()
        if current_time - self.__last_add_time >= 3:
            self.__real_time_speed = 0

        return self.__real_time_speed

    def get_average_speed(self):
        return float(self.__total_flow)/1024/1024/(time.time() - self.__init_time)

    def get_init_time(self):
        return self.__init_time

    def get_total_flow(self):
        return float(self.__total_flow)/1024/1024

    def get_duration(self):
        return time.time() - self.__init_time


