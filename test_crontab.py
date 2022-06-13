from crontab import CronTab
from datetime import date, datetime
import sched, time, math

base = datetime.now()
print(base)
iter = CronTab("*/1 * * * *")
iter2 = CronTab("*/2 * * * *")

print(iter.next(default_utc=True))
print(iter2.next(default_utc=True))
print((int(math.ceil(iter.next(default_utc=True)))))
print(iter2.next(default_utc=True))

def print_time_2(a='default'):
    print("From print_time_2", time.time(), a)
    s.enter(iter2.next(default_utc=True), 0, print_time_2, argument=('defu'))
    print(s.queue)

def print_time(a='default'):
    print("From print_time", time.time(), a)
    s.enter(iter.next(default_utc=True), 0, print_time)
    print(s.queue)


s = sched.scheduler(time.time, time.sleep)
s.enter(iter.next(default_utc=True), 0, print_time)
s.enter(iter2.next(default_utc=True), 0, print_time_2)

print(s.queue)
s.run(True)

print(s.queue)

