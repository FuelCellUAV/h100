import tmp102
from time import sleep

t1 = tmp102.Tmp102Daemon(0x48)
t2 = tmp102.Tmp102Daemon(0x49)
t3 = tmp102.Tmp102Daemon(0x4a)
t4 = tmp102.Tmp102Daemon(0x4b)

t1.daemon = True
t2.daemon = True
t3.daemon = True
t4.daemon = True

t1.start()
t2.start()
t3.start()
t4.start()

while True:
	print(t1())
	print(t2())
	print(t3())
	print(t4())
	print('\n')
	sleep(1)
