from time import sleep

import tmp102

t = tmp102.Tmp102()

while True:
    print(t.get(0x48))
    print(t.get(0x49))
    print(t.get(0x4a))
    print(t.get(0x4b))
    print('\n')
    sleep(1)
