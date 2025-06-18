from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")

celery= Celery(
    "tasks",
    backend=REDIS_URL,
    broker=REDIS_URL
)

import Router.task
