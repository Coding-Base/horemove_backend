import logging

from common.email.service import send_transactional_email
from django.conf import settings
from django.utils.html import strip_tags

logger = logging.getLogger("horemow.donations")


def send_donor_appreciation_email(transaction) -> bool:
    """
    Sends a personalized receipt and heartfelt appreciation email
    to the donor once their payment is verified successful.
    """
    if not transaction.donor_email:
        logger.warning("Cannot send appreciation email: transaction %s has no donor email.", transaction.id)
        return False

    project_name = transaction.project.name if transaction.project else "General Ministry Offering"
    donor_display = (
        "Beloved in Christ" if transaction.is_anonymous or not transaction.donor_name else transaction.donor_name
    )
    formatted_amount = f"{transaction.currency} {transaction.amount:,.2f}"
    reference = transaction.provider_reference

    subject = f"Official Receipt & Appreciation for Your Offering - HOREMOW Ref: {reference}"
    from_email = settings.DEFAULT_FROM_EMAIL

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Thank You for Your Offering</title>
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
        .header {{ background: #0f172a; color: #ffffff; padding: 30px 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 20px; letter-spacing: 1px; color: #f59e0b; text-transform: uppercase; }}
        .header p {{ margin: 8px 0 0; font-size: 13px; color: #cbd5e1; }}
        .content {{ padding: 32px 24px; }}
        .greeting {{ font-size: 17px; font-weight: 600; color: #0f172a; }}
        .receipt-card {{ background: #f1f5f9; border-left: 4px solid #f59e0b; padding: 18px; border-radius: 4px; margin: 24px 0; }}
        .receipt-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }}
        .receipt-label {{ color: #64748b; font-weight: 500; }}
        .receipt-value {{ color: #0f172a; font-weight: 700; }}
        .scripture {{ font-style: italic; color: #475569; background: #fffbeb; border: 1px solid #fde68a; padding: 14px; border-radius: 6px; margin: 20px 0; text-align: center; font-size: 14px; }}
        .footer {{ background: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Holiness Revival Movement Worldwide</h1>
          <p>Spreading Righteousness and True Holiness Across All Nations</p>
        </div>
        <div class="content">
          <p class="greeting">Dear {donor_display},</p>
          <p>
            Grace and peace be multiplied unto you from God our Father and our Lord Jesus Christ.
          </p>
          <p>
            We have gratefully received and confirmed your generous offering in support of the Lord's work through Holiness Revival Movement Worldwide (HOREMOW). Your faithful giving helps us continue reaching souls with the uncompromised message of salvation and holiness across the world.
          </p>
          <div class="receipt-card">
            <table width="100%" cellpadding="4" cellspacing="0" style="font-size: 14px;">
              <tr>
                <td style="color: #64748b;"><strong>Receipt Reference:</strong></td>
                <td style="text-align: right; color: #0f172a; font-family: monospace;"><strong>{reference}</strong></td>
              </tr>
              <tr>
                <td style="color: #64748b;"><strong>Designation / Project:</strong></td>
                <td style="text-align: right; color: #0f172a;">{project_name}</td>
              </tr>
              <tr>
                <td style="color: #64748b;"><strong>Amount Contributed:</strong></td>
                <td style="text-align: right; color: #059669; font-size: 16px; font-weight: bold;">{formatted_amount}</td>
              </tr>
              <tr>
                <td style="color: #64748b;"><strong>Payment Status:</strong></td>
                <td style="text-align: right; color: #0284c7; font-weight: bold;">Confirmed & Verified</td>
              </tr>
            </table>
          </div>

          <div class="scripture">
            "Every man according as he purposeth in his heart, so let him give; not grudgingly, or of necessity: for God loveth a cheerful giver. And God is able to make all grace abound toward you..."
            <br><strong>— 2 Corinthians 9:7-8</strong>
          </div>

          <p>
            May the Almighty God who sees your sacrifice bless you abundantly in your spiritual life, your family, your health, and the labor of your hands. May your garment of holiness remain unspotted until the coming of our Lord.
          </p>
          <p style="margin-top: 28px;">
            In His Service,<br>
            <strong>Pastor Paul Rika</strong><br>
            <em>International Director</em><br>
            Holiness Revival Movement Worldwide
          </p>
        </div>
        <div class="footer">
          <p>This is an automated confirmation of your donation. Please keep this email for your records.</p>
          <p>Official Website: https://horemow.com | Contact: donations@horemow.org</p>
        </div>
      </div>
    </body>
    </html>
    """

    plain_text = strip_tags(html_content)

    result = send_transactional_email(
        to=transaction.donor_email,
        subject=subject,
        html_content=html_content,
        plain_text=plain_text,
        from_email=from_email,
    )

    if result.get("success"):
        transaction.appreciation_email_sent = True
        transaction.save(update_fields=["appreciation_email_sent"])
        logger.info(
            "Successfully sent donor appreciation email via %s for ref %s",
            result.get("provider"),
            reference,
        )
        return True
    else:
        logger.error(
            "Failed to send donor appreciation email for ref %s: %s",
            reference,
            result.get("error"),
        )
        return False
