"""
email_service.py — Email sending via Resend HTTP API.

Why Resend instead of Flask-Mail/SMTP?
Render's Free Tier blocks outbound SMTP ports (25, 465, 587).
Resend uses HTTPS (port 443) which is always allowed.

Setup:
  1. Sign up at https://resend.com (free tier = 3,000 emails/month)
  2. Get your API key
  3. Add to Render env: RESEND_API_KEY=re_xxxxxxxxxxxx
  4. Add to Render env: MAIL_FROM=noreply@yourdomain.com  (or use resend test domain)
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
MAIL_FROM      = os.environ.get("MAIL_FROM", "IEIS Elections <onboarding@resend.dev>")

def _send(to_email: str, subject: str, body: str) -> bool:
    """Core send function via Resend REST API. Returns True on success."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — email not sent.")
        return False
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": MAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "text": body,
            },
            timeout=10,
        )
        if resp.status_code in (200, 201):
            logger.info(f"Email sent via Resend to {to_email} (subject: {subject!r})")
            return True
        else:
            logger.error(f"Resend API error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


# ─── Public helpers (signatures kept identical so app.py needs no changes) ───

def send_registration_email(mail, to_email, voter_name, roll_number):
    """Send registration confirmation. `mail` arg kept for signature compat."""
    subject = "Registration Confirmed — IEIS"
    body = f"""Hello {voter_name},

Your registration in the IEIS Smart Election System has been confirmed.

Roll Number : {roll_number}
Status      : Registered ✓

You will be notified by email whenever an election you are eligible for is announced.
Log in at any time to view active elections and cast your vote.

— IEIS Election Team
Sri Venkatesa Perumal College of Engineering & Technology"""
    _send(to_email, subject, body)


def send_vote_confirmation_email(mail, to_email, voter_name, election_title, candidate_name, timestamp):
    subject = "Vote Confirmed — IEIS"
    body = f"""Hello {voter_name},

Your vote for "{candidate_name}" in the election "{election_title}" has been successfully recorded.

Timestamp   : {timestamp} UTC
Your vote is secure and will be counted in the final results.

— IEIS Election Team
Sri Venkatesa Perumal College of Engineering & Technology"""
    _send(to_email, subject, body)


def send_election_announcement(mail, to_email, voter_name, election_title,
                               description, position_role, start_date, end_date):
    """Notify an eligible voter that a new election has been created."""
    subject = f"New Election Announced: {election_title} — IEIS"
    body = f"""Hello {voter_name},

A new election has been announced and you are eligible to participate!

Election   : {election_title}
Role       : {position_role}
Description: {description}
Starts     : {start_date}
Ends       : {end_date}

Please log in to the IEIS portal to cast your vote during the election period.

— IEIS Election Team
Sri Venkatesa Perumal College of Engineering & Technology"""
    _send(to_email, subject, body)


def send_election_results(mail, to_email, voter_name, election_title,
                          position_role, winner_name, winner_party, total_votes):
    """Notify a voter that results have been published for an election."""
    subject = f"Election Results: {election_title} — IEIS"
    party_line = f"Party/Group : {winner_party}\n" if winner_party else ""
    body = f"""Hello {voter_name},

The results for the election "{election_title}" have been officially published.

Position   : {position_role}
Winner     : {winner_name}
{party_line}Total Votes : {total_votes}

Thank you for participating in making this election a success.

— IEIS Election Team
Sri Venkatesa Perumal College of Engineering & Technology"""
    _send(to_email, subject, body)


def send_care_response_email(to_email, voter_name, complaint_id, status, admin_response):
    """Notify a voter their support case has been updated by customer care."""
    status_word = "resolved" if status == "resolved" else "closed"
    subject = f"Update on your Support Case #{complaint_id} — IEIS"
    body = f"""Hello {voter_name},

Your support case #{complaint_id} has been {status_word}.

Message from Customer Care:
{admin_response}

If you have further questions, please submit a new support request on the IEIS portal.

— IEIS Customer Care
Sri Venkatesa Perumal College of Engineering & Technology"""
    _send(to_email, subject, body)
