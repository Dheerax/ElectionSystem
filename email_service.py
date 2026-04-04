import logging
from flask_mail import Message

logger = logging.getLogger(__name__)


def send_registration_email(mail, to_email, voter_name, roll_number):
    try:
        subject = "Registration Confirmed — IEIS"
        body = f"""Hello {voter_name},

Your registration in the IEIS Smart Election System has been confirmed.

Roll Number : {roll_number}
Status      : Registered ✓

You will be notified by email whenever an election you are eligible for is announced.
Log in at any time to view active elections and cast your vote.

— IEIS Election Team
Sri Venkatesa Perumal College of Engineering & Technology"""
        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
    except Exception as e:
        logger.error(f"Failed to send registration email to {to_email}: {e}")


def send_vote_confirmation_email(mail, to_email, voter_name, election_title, timestamp):
    try:
        subject = "Vote Confirmed — IEIS"
        body = f"""Hello {voter_name},

Your vote in "{election_title}" has been successfully recorded.

Timestamp   : {timestamp} UTC
Your vote is secure and will be counted in the final results.

— IEIS Election Team
Sri Venkatesa Perumal College of Engineering & Technology"""
        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
    except Exception as e:
        logger.error(f"Failed to send vote confirmation email to {to_email}: {e}")


def send_election_announcement(mail, to_email, voter_name, election_title,
                               description, position_role, start_date, end_date):
    """Notify an eligible voter that a new election has been created."""
    try:
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
        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
    except Exception as e:
        logger.error(f"Failed to send election announcement to {to_email}: {e}")


def send_election_results(mail, to_email, voter_name, election_title,
                          position_role, winner_name, winner_party, total_votes):
    """Notify a voter that results have been published for an election."""
    try:
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
        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
    except Exception as e:
        logger.error(f"Failed to send election results email to {to_email}: {e}")
