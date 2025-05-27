from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr # EmailStr is for type annotation and validation by Pydantic
import os 
import logging
from pathlib import Path 

logger = logging.getLogger("health_app.utils.mail")

# --- Email Configuration ---
MAIL_USERNAME_ENV = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD_ENV = os.getenv("MAIL_PASSWORD") 
MAIL_FROM_ENV = os.getenv("MAIL_FROM")
MAIL_SERVER_ENV = os.getenv("MAIL_SERVER", "smtp.gmail.com") 
MAIL_PORT_ENV = int(os.getenv("MAIL_PORT", 587)) 
MAIL_STARTTLS_ENV = os.getenv("MAIL_STARTTLS", "True").lower() == 'true'
MAIL_SSL_TLS_ENV = os.getenv("MAIL_SSL_TLS", "False").lower() == 'true'
MAIL_FROM_NAME_ENV = os.getenv("MAIL_FROM_NAME", "Health App System")

if not all([MAIL_USERNAME_ENV, MAIL_PASSWORD_ENV, MAIL_FROM_ENV]):
    logger.error(
        "Email credentials (MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM) are not fully set in environment variables. "
        "Email sending will likely fail."
    )

# TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME_ENV,
    MAIL_PASSWORD=MAIL_PASSWORD_ENV,
    # Corrected usage: Assign the string directly. Pydantic validates against EmailStr type.
    MAIL_FROM=(MAIL_FROM_ENV if MAIL_FROM_ENV else "default_from@example.com"), # <--- CORRECTED LINE
    MAIL_PORT=MAIL_PORT_ENV,
    MAIL_SERVER=MAIL_SERVER_ENV,
    MAIL_FROM_NAME=MAIL_FROM_NAME_ENV,
    MAIL_STARTTLS=MAIL_STARTTLS_ENV,
    MAIL_SSL_TLS=MAIL_SSL_TLS_ENV,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True, 
    # TEMPLATE_FOLDER=TEMPLATE_DIR 
)

fm = FastMail(conf)

async def send_patient_welcome_email(email_to: EmailStr, patient_name: str):
    if not all([MAIL_USERNAME_ENV, MAIL_PASSWORD_ENV, MAIL_FROM_ENV]):
        logger.error(f"Cannot send welcome email to {email_to}: Email service is not configured (missing credentials).")
        return 

    subject = f"Welcome to Health App, {patient_name}!"
    
    html_body = f"""
    <html>
        <body>
            <h2>Welcome, {patient_name}!</h2>
            <p>Thank you for registering with the Health App. Your patient profile has been successfully created.</p>
            <p>We are pleased to have you on board.</p>
            <p>If you have any questions, feel free to contact our support.</p>
            <p>Best regards,<br/>The Health App Team</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],  
        body=html_body,
        subtype=MessageType.html 
    )

    try:
        logger.info(f"Attempting to send welcome email to: {email_to} for patient: {patient_name}")
        await fm.send_message(message)
        logger.info(f"Welcome email successfully sent to: {email_to}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email_to}: {e}", exc_info=True)

