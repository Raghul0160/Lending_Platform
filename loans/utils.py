import random
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP, User

def send_otp_email(email):
    try:
        # Generate 6 digit code
        otp_code = str(random.randint(100000, 999999))
        user = User.objects.get(email=email)
        
        # Save OTP to Database (Delete old one if exists)
        OTP.objects.filter(user=user).delete()
        OTP.objects.create(user=user, otp_code=otp_code)
        
        # Send Email
        subject = 'Verify Your Account'
        message = f'Welcome to the Lending Platform! Your verification code is: {otp_code}'
        from_email = settings.EMAIL_HOST_USER
        
        send_mail(subject, message, from_email, [email])
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False