from django.core.mail import EmailMessage
from django.conf import settings

def send_error_mail(request,msg):
    msg += '\n\nrequest.user: ' + str(request.user)
    msg += '\n\nrequest.path: ' + str(request.path)
    title = 'Geonition error'
    mail = EmailMessage(title, msg, to=[getattr(settings,'ADMINS',(('master','webmaster@mapita.fi'),))[0][1]])
    mail.send()

