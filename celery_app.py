from celery import Celery

celery= Celery(
    "tasks",
    backend="redis://redis:6379/0",
    broker="redis://redis:6379/0"
)

import Router.task
