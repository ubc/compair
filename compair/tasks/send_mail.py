from compair.core import celery, mail
from flask_mail import Message
from flask import current_app

@celery.task(bind=True, ignore_result=True)
def send_messages(self, messages):
    with mail.connect() as conn:
        for message in messages:
            msg = Message(
                recipients=message.get('recipients'),
                subject=message.get('subject'),
                html=message.get('html_body'),
                body=message.get('text_body')
            )
            conn.send(msg)


@celery.task(bind=True, ignore_result=True)
def send_message(self, recipients, subject, html_body, text_body):
    # send message
    msg = Message(
        recipients=recipients,
        subject=subject,
        html=html_body,
        body=text_body
    )
    mail.send(msg)