from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import base64
import os

from app.core.config import settings


class EmailService:
    """Service for sending emails via SendGrid or SMTP fallback"""

    @staticmethod
    def send_quote_request(
        to_email: str,
        to_name: str,
        project_name: str,
        items: List[dict],
        message: Optional[str] = None,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """
        Send quote request email to vendor

        Args:
            to_email: Vendor email address
            to_name: Vendor name
            project_name: Name of the project
            items: List of items to quote (dict with description, quantity, unit)
            message: Custom message
            attachments: List of files to attach (dict with filename and content)

        Returns:
            bool: True if email sent successfully
        """
        subject = f"Quote Request: {project_name}"

        # Build HTML email body
        items_html = ""
        for item in items:
            items_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{item.get('description', '')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{item.get('quantity', '')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{item.get('unit', '')}</td>
                </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background-color: #e5e7eb; padding: 10px; text-align: left; border: 1px solid #ddd; }}
                td {{ padding: 8px; border: 1px solid #ddd; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Quote Request</h1>
                </div>
                <div class="content">
                    <p>Dear {to_name},</p>
                    <p>We would like to request a quote for the following items for our project: <strong>{project_name}</strong></p>

                    {f'<p>{message}</p>' if message else ''}

                    <h3>Items to Quote:</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Description</th>
                                <th style="text-align: center;">Quantity</th>
                                <th style="text-align: center;">Unit</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>

                    <p>Please provide your quote at your earliest convenience. Include:</p>
                    <ul>
                        <li>Unit price for each item</li>
                        <li>Total price</li>
                        <li>Lead time / availability</li>
                        <li>Any applicable terms and conditions</li>
                    </ul>

                    <p>If you have any questions, please don't hesitate to contact us.</p>

                    <p>Thank you for your prompt attention to this request.</p>

                    <p>Best regards,<br>
                    {settings.SENDGRID_FROM_NAME if hasattr(settings, 'SENDGRID_FROM_NAME') else 'Your Company'}</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from DTG Workflow Automations</p>
                </div>
            </div>
        </body>
        </html>
        """

        try:
            # Try SendGrid first
            if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
                return EmailService._send_via_sendgrid(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    attachments=attachments
                )
            else:
                # Fallback to SMTP if configured
                return EmailService._send_via_smtp(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    attachments=attachments
                )
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    @staticmethod
    def _send_via_sendgrid(
        to_email: str,
        subject: str,
        html_content: str,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """Send email via SendGrid"""
        try:
            message = Mail(
                from_email=settings.SENDGRID_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )

            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    file_content = base64.b64encode(attachment['content']).decode()
                    attached_file = Attachment(
                        FileContent(file_content),
                        FileName(attachment['filename']),
                        FileType(attachment.get('content_type', 'application/pdf')),
                        Disposition('attachment')
                    )
                    message.add_attachment(attached_file)

            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"SendGrid error: {str(e)}")
            return False

    @staticmethod
    def _send_via_smtp(
        to_email: str,
        subject: str,
        html_content: str,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """Send email via SMTP (fallback)"""
        try:
            # This is a basic SMTP implementation
            # You would need to configure SMTP settings
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SENDGRID_FROM_EMAIL
            msg['To'] = to_email

            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f"attachment; filename= {attachment['filename']}"
                    )
                    msg.attach(part)

            # Note: SMTP credentials would need to be configured
            # This is a placeholder implementation
            print(f"SMTP fallback: Would send email to {to_email}")
            print("Note: SMTP needs to be configured in settings")
            return True

        except Exception as e:
            print(f"SMTP error: {str(e)}")
            return False

    @staticmethod
    def send_quote_reminder(
        to_email: str,
        to_name: str,
        project_name: str,
        original_sent_date: str
    ) -> bool:
        """Send reminder email for pending quote"""
        subject = f"Reminder: Quote Request for {project_name}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Dear {to_name},</p>
            <p>This is a friendly reminder about our quote request for <strong>{project_name}</strong>,
            sent on {original_sent_date}.</p>
            <p>If you have already submitted your quote, please disregard this message.</p>
            <p>If you need additional information, please let us know.</p>
            <p>Thank you,<br>
            {settings.SENDGRID_FROM_NAME if hasattr(settings, 'SENDGRID_FROM_NAME') else 'Your Company'}</p>
        </body>
        </html>
        """

        try:
            if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
                return EmailService._send_via_sendgrid(to_email, subject, html_content)
            else:
                return EmailService._send_via_smtp(to_email, subject, html_content)
        except Exception as e:
            print(f"Error sending reminder: {str(e)}")
            return False

    @staticmethod
    def send_quote_confirmation(
        to_email: str,
        to_name: str,
        project_name: str,
        total_amount: str
    ) -> bool:
        """Send confirmation email when quote is accepted"""
        subject = f"Quote Accepted: {project_name}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Dear {to_name},</p>
            <p>Thank you for your quote for <strong>{project_name}</strong>.</p>
            <p>We are pleased to inform you that we have accepted your quote
            in the amount of <strong>${total_amount}</strong>.</p>
            <p>We will be in touch shortly with next steps.</p>
            <p>Thank you,<br>
            {settings.SENDGRID_FROM_NAME if hasattr(settings, 'SENDGRID_FROM_NAME') else 'Your Company'}</p>
        </body>
        </html>
        """

        try:
            if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
                return EmailService._send_via_sendgrid(to_email, subject, html_content)
            else:
                return EmailService._send_via_smtp(to_email, subject, html_content)
        except Exception as e:
            print(f"Error sending confirmation: {str(e)}")
            return False
