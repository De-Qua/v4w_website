from flask_mail import Message
from app import app,email
import pdb

our_email = app.config["ADMINS"][0]

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    email.send(msg)

def send_email_to_ourself(subject,html_body):
    send_email(subject=subject, sender=our_email, recipients=[our_email], text_body="", html_body=html_body)
