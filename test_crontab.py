from croniter import croniter
from datetime import date, datetime
import sched, time

base = datetime.now()
print(base)
iter = croniter("*/1 * * * *", base)
iter2 = croniter("*/5 * * * *", base)

print(iter.get_next(datetime))
print(iter2.get_next(datetime))
print(iter.get_next(datetime))
print(iter2.get_next(datetime))

def print_time(a='default'):
     print("From print_time", time.time(), a)


s = sched.scheduler(time.time, time.sleep)
s.enterabs(iter.get_next(float), 0, print_time)
s.enterabs(iter2.get_next(float), 0, print_time)
s.enterabs(iter.get_next(float), 0, print_time)
s.enterabs(iter.get_next(float), 0, print_time)

print(s.queue)
s.run(True)

print(s.queue)

