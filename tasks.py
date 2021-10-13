from celery import Celery
from core.send_email import send_email_async

app = Celery('tasks', backend='redis://localhost', broker='redis://localhost')

@app.task
async def send_mail(email, text):
    await send_email_async(email, text)