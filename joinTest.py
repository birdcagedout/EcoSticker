import time
import threading


def non_daemon():
	while True:
		time.sleep(1)
		print ('Test non-daemon')
	print('=== end of thread ===')

t = threading.Thread(name='daemon', daemon=True, target=non_daemon)

print('--- t.start() ---')
t.start()

print('--- time.sleep(3) ---')
time.sleep(3)

print('--- t.join() started ---')
t.join()
print('--- t.join() ended ---')

print('end of main')


