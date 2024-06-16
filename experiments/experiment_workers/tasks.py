from celery import Celery
import time

app = Celery('tasks', backend='rpc://guest@localhost//', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):
    time.sleep(5)
    return x + y