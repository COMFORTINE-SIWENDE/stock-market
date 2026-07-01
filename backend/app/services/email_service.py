"""Email service"""

from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.EMAIL_HOST
        self.smtp_port = settings.EMAIL_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.use_tls = settings.EMAIL_USE_TLS
        self.use_ssl = settings.EMAIL_USE_SSL
        
    def _get_connection(self):
        """Return the correct SMTP connection object."""
        if getattr(self, 'use_ssl', False):
            return smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30)
        else:
            return smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)

    def send_otp_email(self, email: str, otp_code: str) -> bool:
        """Send OTP email for KCAA-SRBS"""
        subject = "Your KCAA-SRBS Login OTP Code"
        body = self._create_otp_email_template(otp_code)
        return self.send_email(email, subject, body)

    def send_password_reset_request_email(self, email: str) -> bool:
        """Notify admin about password reset request"""
        subject = "Password Reset Request - KCAA-SRBS"
        body = self._create_password_reset_request_template(email)
        return self.send_email(settings.ADMIN_EMAIL, subject, body)

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = f"KCAA-SRBS <{settings.EMAIL_FROM}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}")

            with self._get_connection() as server:
                server.set_debuglevel(1)

                if self.use_tls and not self.use_ssl:
                    logger.info("Starting TLS...")
                    server.starttls()

                logger.info(f"Logging in as {self.username}")
                server.login(self.username, self.password)

                logger.info("Sending email...")
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False

    def _create_otp_email_template(self, otp_code: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>KCAA-SRBS Login OTP</title>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">KCAA Staff Retirement Benefit Scheme</h2>
                <p>Your one-time password (OTP) for login is:</p>
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 28px; letter-spacing: 8px; margin: 20px 0; border: 2px dashed #dee2e6;">
                    <strong>{otp_code}</strong>
                </div>
                <p>This OTP is valid for {settings.OTP_EXPIRE_MINUTES} minutes. Do not share it with anyone.</p>
                <p>If you didn't request this OTP, please contact the system administrator immediately.</p>
                <hr>
                <p style="color: #6c757d; font-size: 12px;">KCAA Staff Retirement Benefit Scheme System</p>
            </div>
        </body>
        </html>
        """

    def _create_password_reset_request_template(self, email: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset Request</title>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Password Reset Request - KCAA-SRBS</h2>
                <p>A user has requested a password reset:</p>
                
                <div style="background-color: #fff3cd; padding: 15px; margin: 15px 0; border: 1px solid #ffeaa7;">
                    <p><strong>User Email:</strong> {email}</p>
                    <p><strong>Request Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <p>Please process this request through the admin panel:</p>
                <ol>
                    <li>Verify the user's identity</li>
                    <li>Reset their password in the system</li>
                    <li>The user will receive a temporary password and OTP via email</li>
                </ol>
                
                <hr>
                <p style="color: #6c757d; font-size: 12px;">KCAA Staff Retirement Benefit Scheme System</p>
            </div>
        </body>
        </html>
        """

    def send_account_suspension_email(self, email: str, reason: str, effective_immediately: bool) -> bool:
        """Send account suspension notification email."""
        subject = "KCAA-SRBS Account Suspension Notice"
        body = self._create_suspension_email_template(reason, effective_immediately)
        return self.send_email(email, subject, body)

    def send_account_activation_email(self, email: str) -> bool:
        """Send account activation welcome email."""
        subject = "KCAA-SRBS Account Activated"
        body = self._create_activation_email_template()
        return self.send_email(email, subject, body)

    def send_role_change_notification(self, email: str, previous_role: str, new_role: str) -> bool:
        """Send role change notification email."""
        subject = "KCAA-SRBS Role Change Notification"
        body = self._create_role_change_template(previous_role, new_role)
        return self.send_email(email, subject, body)

    def _create_suspension_email_template(self, reason: str, effective_immediately: bool) -> str:
        effective_text = "immediately" if effective_immediately else "on the specified date"
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Account Suspension Notice</title>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #dc3545;">KCAA Staff Retirement Benefit Scheme - Account Suspension</h2>
                <p>Your account access has been suspended {effective_text}.</p>
                
                <div style="background-color: #f8d7da; padding: 15px; margin: 15px 0; border-left: 4px solid #dc3545;">
                    <p><strong>Reason for Suspension:</strong> {reason}</p>
                </div>
                
                <p>During this suspension period, you will not be able to access the KCAA-SRBS system.</p>
                
                <p>If you believe this is an error or would like to appeal this decision, 
                please contact the system administrator.</p>
                
                <hr>
                <p style="color: #6c757d; font-size: 12px;">KCAA Staff Retirement Benefit Scheme System</p>
            </div>
        </body>
        </html>
        """

    def _create_activation_email_template(self) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Account Activated</title>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">Welcome to KCAA Staff Retirement Benefit Scheme</h2>
                <p>Your account has been activated and you can now access the KCAA-SRBS system.</p>
                
                <div style="background-color: #d4edda; padding: 15px; margin: 15px 0; border-left: 4px solid #28a745;">
                    <p><strong>Next Steps:</strong></p>
                    <ol>
                        <li>Login to the system using your credentials</li>
                        <li>Complete your profile information</li>
                        <li>Explore the available features based on your role</li>
                    </ol>
                </div>
                
                <p>If you encounter any issues during login, please contact the system administrator.</p>
                
                <hr>
                <p style="color: #6c757d; font-size: 12px;">KCAA Staff Retirement Benefit Scheme System</p>
            </div>
        </body>
        </html>
        """

    def _create_role_change_template(self, previous_role: str, new_role: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Role Change Notification</title>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #17a2b8;">KCAA-SRBS Role Change Notification</h2>
                <p>Your user role in the KCAA Staff Retirement Benefit Scheme system has been updated.</p>
                
                <div style="background-color: #d1ecf1; padding: 15px; margin: 15px 0; border-left: 4px solid #17a2b8;">
                    <p><strong>Previous Role:</strong> {previous_role}</p>
                    <p><strong>New Role:</strong> {new_role}</p>
                </div>
                
                <p>This change may affect the features and permissions available to you in the system.</p>
                
                <p>If you have any questions about your new role, please contact the system administrator.</p>
                
                <hr>
                <p style="color: #6c757d; font-size: 12px;">KCAA Staff Retirement Benefit Scheme System</p>
            </div>
        </body>
        </html>
        """


    def _create_temporary_password_email_template(self, temporary_password: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Your KCAA-SRBS Account</title>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Welcome to KCAA Staff Retirement Benefit Scheme</h2>
                <p>Your account has been created. Here are your login credentials:</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-left: 4px solid #007bff;">
                    <p style="text-align: center; font-size: 24px; letter-spacing: 4px; margin: 0;">
                        <strong>{temporary_password}</strong>
                    </p>
                    <p style="text-align: center; color: #6c757d; margin: 10px 0 0 0;">Temporary Password</p>
                </div>
                
                <p><strong>Login Instructions:</strong></p>
                <ol>
                    <li>Go to the KCAA-SRBS login page</li>
                    <li>Enter your email address</li>
                    <li>Use the temporary password above to login</li>
                    <li>You will be required to set your permanent password on first login</li>
                </ol>
                
                <p><strong>Important Security Notes:</strong></p>
                <ul>
                    <li>Your temporary password will expire in 7 days</li>
                    <li>You must change your password on first login</li>
                    <li>Do not share this password with anyone</li>
                    <li>If you didn't request this account, please contact administrator immediately</li>
                </ul>
                
                <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border: 1px solid #ffeaa7;">
                    <p style="margin: 0; color: #856404;">
                        <strong>Note:</strong> For security reasons, you will need to request an OTP 
                        on your first login to verify your identity and set a new password.
                    </p>
                </div>
                
                <hr>
                <p style="color: #6c757d; font-size: 12px;">KCAA Staff Retirement Benefit Scheme System</p>
            </div>
        </body>
        </html>
        """
    def send_temporary_password_email(self, email: str, temporary_password: str) -> bool:
        """Send temporary password email for new users/password reset"""
        subject = "Your KCAA-SRBS Account Credentials"
        body = self._create_temporary_password_email_template(temporary_password)
        return self.send_email(email, subject, body)
    # Global email service instance
email_service = EmailService()