import tmp102
from time import sleep

t1 = tmp102.Tmp102(0x48)
t2 = tmp102.Tmp102(0x49)
t3 = tmp102.Tmp102(0x4a)
t4 = tmp102.Tmp102(0x4b)

while True:
	print(t1.get())
	print(t2.get())
	print(t3.get())
	print(t4.get())
	print('\n')
	sleep(1)
