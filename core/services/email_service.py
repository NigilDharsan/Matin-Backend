import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class EmailService:
    """Service class for handling email operations"""

    @staticmethod
    def generate_otp(length=6):
        """Generate a random OTP"""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def send_otp_email(email, otp):
        """Send OTP to user's email"""
        subject = 'Password Reset OTP'
        message = f'''
        Hello,

        Your OTP for password reset is: {otp}

        This OTP is valid for 10 minutes.

        If you didn't request this, please ignore this email.

        Best regards,
        Dealer Management Team
        '''
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    @staticmethod
    def is_otp_valid(user, otp):
        """Check if OTP is valid and not expired"""
        if not user.otp or user.otp != otp:
            return False
        
        if not user.otp_created_at:
            return False
        
        # Check if OTP is expired (10 minutes validity)
        expiry_time = user.otp_created_at + timedelta(minutes=10)
        if timezone.now() > expiry_time:
            return False
        
        return True

    @staticmethod
    def clear_otp(user):
        """Clear OTP data from user"""
        user.otp = None
        user.otp_created_at = None
        user.save(update_fields=['otp', 'otp_created_at'])