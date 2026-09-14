import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_EMAIL = "b94cf1001@smtp-brevo.com"
SMTP_PASSWORD = "xsmtpsib-a4d827a94d868ed94b652c603a172f8fd2f2b770eb137cc4a49ac8a7d52bc2ab-D5B2l8ogZD6Fw2rg"

EMAIL_FROM = "simdaa.solvo@outlook.com"


def send_email(to_email, subject, body):

    msg = MIMEMultipart()

    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()

    server.login(SMTP_EMAIL, SMTP_PASSWORD)

    server.sendmail(
        EMAIL_FROM,
        to_email,
        msg.as_string()
    )

    server.quit()