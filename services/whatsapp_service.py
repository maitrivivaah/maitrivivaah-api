from config import get_settings

settings = get_settings()


def send_whatsapp_notification(to: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    Returns True on success, False on failure (non-blocking).
    """
    if not settings.twilio_account_sid:
        print(f"[WhatsApp stub] To: {to} | Msg: {message}")
        return True

    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=message,
            from_=settings.whatsapp_from,
            to=f"whatsapp:{to}",
        )
        return True
    except Exception as e:
        print(f"[WhatsApp error] {e}")
        return False


def notify_admin_new_registration(user_name: str, email: str, plan: str):
    msg = (
        f"🪷 *New MaitriVivaah Registration*\n\n"
        f"Name: {user_name}\n"
        f"Email: {email}\n"
        f"Plan: {plan.upper()}\n"
        f"Please review the profile in the admin panel."
    )
    send_whatsapp_notification(settings.admin_whatsapp, msg)


def notify_user_registration(phone: str, user_name: str):
    msg = (
        f"🪷 Welcome to MaitriVivaah, {user_name}!\n\n"
        f"Your profile has been submitted and is under review. "
        f"Our team will reach out within 24 hours.\n\n"
        f"For queries, reply to this message."
    )
    send_whatsapp_notification(phone, msg)


def notify_interest_received(phone: str, sender_name: str):
    msg = (
        f"💌 *{sender_name}* has expressed interest in your MaitriVivaah profile!\n\n"
        f"Login to view their profile and respond."
    )
    send_whatsapp_notification(phone, msg)
