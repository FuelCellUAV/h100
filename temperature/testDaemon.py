from time import sleep

import tmp102


t = tmp102.Tmp102Daemon()

t.daemon = True

t.start()

while True:
    print(t()[0])
    print(t()[1])
    print(t()[2])
    print(t()[3])
    print('\n')
    sleep(1)
