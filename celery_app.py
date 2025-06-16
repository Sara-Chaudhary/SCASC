from celery import Celery

celery= Celery(
    "tasks",
    backend="redis://localhost:6379/0",
    broker="redis://localhost:6379/0"
)

import Router.task
