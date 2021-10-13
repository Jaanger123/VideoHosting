from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from decouple import config


conf = ConnectionConfig(
    MAIL_USERNAME=config('MAIL_USERNAME'),
    MAIL_PASSWORD=config('MAIL_PASSWORD'),
    MAIL_FROM_NAME='VideoHosting',
    MAIL_FROM='video_hosting@gmail.com',
    MAIL_PORT=587,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_TLS=True,
    MAIL_SSL=False,
    TEMPLATE_FOLDER='./templates'
)

async def send_email_async(email_to: str, body: dict):
    message = MessageSchema(
        subject='USER CREATED',
        recipients=[email_to],
        body=body,
        subtype='html',
    )
    
    fm = FastMail(conf)
    await fm.send_message(message, template_name='email.html')