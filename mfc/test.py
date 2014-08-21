import mfc
from time import sleep, time

x=mfc.mfc()

while True:
    sleep(1)
    timeStart = time()
    x.printall()
    print('Loop time was %8.2fms' % ((time() - timeStart)*1000.0))
