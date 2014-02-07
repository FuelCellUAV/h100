#!/usr/bin/python3

from time import time

# Class to control purge frequency
class Purge:
    errorLast = 0
    integral = 0
    timeLast = 0

    def __init__(self, p, i, d, zero=0):
        self.Kp = p
        self.Ki = i
        self.Kd = d
        self.zero = zero
        timeLast = time()

    def __call__(self, error):
        dt = time() - self.timeLast

        self.integral += error * dt
        derivative = (error - self.errorLast) / dt
        self.errorLast = error

        clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
        self.integral = clamp(self.integral, (error * 0.9), (error * 1.1))

        print('%02f' % (error * self.Kp), end='\t')
        print('%02f' % (self.integral * self.Ki), end='\t')
        print('%02f' % (derivative * self.Kd), end='\t')
        return self.zero + self.Kp * error + self.Ki * self.integral + self.Kd * derivative

    def doReset(self):
        self.error = 0
        self.errorLast = 0
        self.integral = 0
        self.derivative = 0
