"""
routers/notifications.py — Email notifications via SMTP.
Sends transactional emails: order ready, reservation confirmed, receipt, etc.
All sent emails are logged in the notifications table.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from database import supabase
from auth import verify_admin
from models import SendNotificationRequest, SendTestEmailRequest
from config import settings

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ── Email Templates ─────────────────────────────────────────────────────────

EMAIL_TEMPLATES = {
    "order_ready": {
        "subject": "Your order #{order_id} is ready! 🎉",
        "body": """
<div style="font-family:'Work Sans',Arial,sans-serif;max-width:480px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1)">
  <div style="background:linear-gradient(135deg,#5d4037,#8d6e63);padding:28px 24px;text-align:center">
    <div style="width:56px;height:56px;background:rgba(255,255,255,.15);border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;justify-content:center">
      <span style="font-size:28px">☕</span>
    </div>
    <h1 style="color:#fff;font-size:22px;font-weight:900;margin:0">Ready for Pickup!</h1>
  </div>
  <div style="padding:28px 24px;text-align:center">
    <p style="color:#475569;font-size:15px;margin:0 0 8px">Hi <strong>{customer_name}</strong>,</p>
    <p style="color:#475569;font-size:14px;margin:0 0 20px">Your order <strong style="color:#5d4037">#{order_id}</strong> is ready and waiting for you at <strong>Table {table_number}</strong>.</p>
    <div style="background:#faf8f5;border:1px solid rgba(93,64,55,.1);border-radius:12px;padding:16px;margin-bottom:20px;text-align:left">
      {items_html}
    </div>
    <div style="border-top:1px solid #f1f0ee;padding-top:16px">
      <div style="display:flex;justify-content:space-between;margin-bottom:6px"><span style="color:#94a3b8;font-size:13px">Subtotal</span><span style="color:#475569;font-size:13px">₹{subtotal}</span></div>
      <div style="display:flex;justify-content:space-between;margin-bottom:10px"><span style="color:#94a3b8;font-size:13px">Tax (9%)</span><span style="color:#475569;font-size:13px">₹{tax}</span></div>
      <div style="display:flex;justify-content:space-between"><span style="color:#1e293b;font-size:15px;font-weight:800">Total</span><span style="color:#5d4037;font-size:15px;font-weight:900">₹{total}</span></div>
    </div>
  </div>
  <div style="background:#faf8f5;padding:16px 24px;text-align:center">
    <p style="color:#94a3b8;font-size:11px;margin:0">Questions? Call us at {cafe_phone}</p>
  </div>
</div>""",
    },

    "reservation_confirmed": {
        "subject": "Reservation confirmed at Smart Cafe ✅",
        "body": """
<div style="font-family:'Work Sans',Arial,sans-serif;max-width:480px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1)">
  <div style="background:linear-gradient(135deg,#3e2723,#6d4c41);height:100px;position:relative">
    <div style="position:absolute;bottom:12px;left:16px;background:#5d4037;color:#fff;font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.1em;padding:3px 8px;border-radius:4px">Confirmed</div>
  </div>
  <div style="padding:24px">
    <h2 style="color:#1e293b;font-size:20px;font-weight:900;margin:0 0 4px">Reservation Confirmed</h2>
    <p style="color:#64748b;font-size:13px;margin:0 0 20px">Smart Cafe • {reservation_date}</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px">
      <div style="border:1.5px solid rgba(93,64,55,.12);border-radius:10px;padding:12px">
        <div style="color:#94a3b8;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">Time</div>
        <div style="color:#1e293b;font-size:16px;font-weight:800">{reservation_time}</div>
      </div>
      <div style="border:1.5px solid rgba(93,64,55,.12);border-radius:10px;padding:12px">
        <div style="color:#94a3b8;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">Guests</div>
        <div style="color:#1e293b;font-size:16px;font-weight:800">{guest_count} People</div>
      </div>
    </div>
    <p style="color:#64748b;font-size:13px">Hi <strong>{customer_name}</strong>, your table has been reserved. We look forward to seeing you!</p>
    {special_requests_html}
  </div>
  <div style="background:#faf8f5;padding:16px 24px;text-align:center">
    <p style="color:#94a3b8;font-size:11px;margin:0">To modify: call {cafe_phone} • {cafe_address}</p>
  </div>
</div>""",
    },

    "reservation_reminder": {
        "subject": "Reminder: Your table is reserved today at {reservation_time} 🕖",
        "body": """
<div style="font-family:'Work Sans',Arial,sans-serif;max-width:480px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden">
  <div style="background:linear-gradient(135deg,#5d4037,#8d6e63);padding:24px;text-align:center">
    <span style="font-size:36px">⏰</span>
    <h2 style="color:#fff;margin:8px 0 0;font-size:20px;font-weight:900">Reservation Reminder</h2>
  </div>
  <div style="padding:24px">
    <p style="color:#475569">Hi <strong>{customer_name}</strong>! Just a reminder that your table is reserved <strong>today at {reservation_time}</strong> for <strong>{guest_count} guests</strong>.</p>
    <p style="color:#94a3b8;font-size:13px">Your table will be held for 15 minutes past your booking time.</p>
  </div>
  <div style="background:#faf8f5;padding:16px 24px;text-align:center">
    <p style="color:#94a3b8;font-size:11px;margin:0">Need to cancel? Call {cafe_phone}</p>
  </div>
</div>""",
    },

    "order_preparing": {
        "subject": "Your order #{order_id} is being prepared 👨‍🍳",
        "body": """
<div style="font-family:'Work Sans',Arial,sans-serif;max-width:480px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden">
  <div style="background:linear-gradient(135deg,#e65100,#bf360c);padding:24px;text-align:center">
    <span style="font-size:36px">👨‍🍳</span>
    <h2 style="color:#fff;margin:8px 0 0;font-size:20px;font-weight:900">Cooking Started!</h2>
  </div>
  <div style="padding:24px;text-align:center">
    <p style="color:#475569">Hi <strong>{customer_name}</strong>! Our chef has started working on your order <strong style="color:#5d4037">#{order_id}</strong>.</p>
    <p style="color:#94a3b8;font-size:13px">Estimated time: <strong>{prep_time} minutes</strong></p>
    <div style="background:#f1ebe7;border-radius:8px;height:8px;margin:16px 0;overflow:hidden">
      <div style="background:#5d4037;width:40%;height:100%;border-radius:8px"></div>
    </div>
    <p style="color:#94a3b8;font-size:12px">You'll receive another email when your order is ready.</p>
  </div>
</div>""",
    },
}


def _build_html(template_type: str, variables: dict) -> tuple[str, str]:
    """Build subject + body HTML from template type and variables."""
    template = EMAIL_TEMPLATES.get(template_type)
    if not template:
        raise ValueError(f"Unknown template type: {template_type}")

    # Default cafe variables
    cafe = {
        "cafe_name":    settings.FROM_NAME,
        "cafe_phone":   "+91 98765 43210",
        "cafe_address": "42, MG Road, Bhubaneswar",
        **variables
    }

    subject = template["subject"]
    body    = template["body"]

    for key, val in cafe.items():
        subject = subject.replace(f"{{{key}}}", str(val))
        body    = body.replace(f"{{{key}}}", str(val))

    return subject, body


def _send_email_sync(to: str, subject: str, html_body: str) -> bool:
    """Send email via SMTP. Returns True on success."""
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        print(f"[EMAIL SKIPPED — no SMTP configured] To: {to} | Subject: {subject}")
        return True  # Don't crash if email not configured

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>"
        msg["To"]      = to
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.FROM_EMAIL, to, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def _log_notification(type_: str, recipient: str, subject: str, variables: dict, status: str):
    """Log to notifications table (fire-and-forget)."""
    try:
        supabase.table("notifications").insert({
            "type":       type_,
            "recipient":  recipient,
            "subject":    subject,
            "body_json":  variables,
            "status":     status,
            "sent_at":    datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        print(f"[NOTIFICATION LOG ERROR] {e}")


async def send_notification_background(type_: str, recipient: str, variables: dict):
    """Background task: build, send, and log a notification email."""
    try:
        subject, body = _build_html(type_, variables)
        ok = _send_email_sync(recipient, subject, body)
        _log_notification(type_, recipient, subject, variables, "sent" if ok else "failed")
    except Exception as e:
        print(f"[NOTIFICATION ERROR] {e}")
        _log_notification(type_, recipient, str(e), variables, "failed")


# ── Public helper used by other routers ─────────────────────────────────────

def trigger_notification(background_tasks: BackgroundTasks, type_: str, recipient: str, variables: dict):
    """Call this from any router to queue an email notification."""
    if recipient and "@" in recipient:
        background_tasks.add_task(send_notification_background, type_, recipient, variables)


# ── REST Endpoints ───────────────────────────────────────────────────────────

@router.post("/send", summary="Admin: send a notification email")
async def send_notification(
    req: SendNotificationRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_admin)
):
    background_tasks.add_task(
        send_notification_background, req.type, req.recipient_email, req.variables
    )
    return {"message": f"Queued {req.type} email to {req.recipient_email}"}


@router.post("/test", summary="Admin: send a test email")
async def send_test_email(
    req: SendTestEmailRequest,
    _: str = Depends(verify_admin)
):
    try:
        subject, body = _build_html(req.template_type, req.variables)
        ok = _send_email_sync(req.recipient_email, subject, body)
        _log_notification(req.template_type, req.recipient_email, subject, req.variables,
                        "sent" if ok else "failed")
        return {"success": ok, "subject": subject, "recipient": req.recipient_email}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/log", summary="Admin: get sent notifications log")
def notification_log(limit: int = 50, _: str = Depends(verify_admin)):
    return supabase.table("notifications")\
        .select("*").order("sent_at", desc=True).limit(limit).execute().data


@router.get("/templates", summary="Get available template types")
def list_templates(_: str = Depends(verify_admin)):
    return [
        {"type": k, "subject_preview": v["subject"]}
        for k, v in EMAIL_TEMPLATES.items()
    ]