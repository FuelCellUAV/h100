from time import sleep, time

import tmp102

t = tmp102.Tmp102()

while True:
    sleep(1)
    timeStart = time()
    print(t.get(0x48), end='\t')
    print(t.get(0x49), end='\t')
    print(t.get(0x4a), end='\t')
    print(t.get(0x4b))
    print('Loop time was %8.2fms' % ((time() - timeStart)*1000.0))
