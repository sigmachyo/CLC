"""
church_app/validators.py

Кастомные валидаторы для форм KCLC.
"""
from django.core.exceptions import ValidationError

# Популярные домены одноразовой почты — пополняй по мере необходимости
DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "guerrillamail.net",
    "guerrillamail.org", "guerrillamail.de", "guerrillamail.info",
    "guerrillamail.biz", "sharklasers.com", "spam4.me",
    "trashmail.com", "trashmail.me", "trashmail.net", "trashmail.io",
    "trashmail.at", "trashmail.de", "trashmail.org",
    "tempmail.com", "temp-mail.org", "temp-mail.io",
    "throwam.com", "throwam.net",
    "dispostable.com", "discard.email",
    "mailnull.com", "mailnull.net",
    "yopmail.com", "yopmail.fr", "yopmail.net",
    "10minutemail.com", "10minutemail.net", "10minutemail.org",
    "20minutemail.com", "20minutemail.it",
    "fakeinbox.com", "fakemail.net",
    "spamgourmet.com", "spamgourmet.net", "spamgourmet.org",
    "mailnesia.com", "mailnull.com",
    "nada.email", "nadam.email",
    "inboxkitten.com",
    "spambox.us", "spambox.me",
    "getairmail.com",
    "filzmail.com",
    "throwaway.email",
    "discard.email",
    "maildrop.cc",
    "anonbox.net",
    "getnada.com",
    "mailsac.com",
    "harakirimail.com",
    "crazymailing.com",
    "bccto.me",
    "chacuo.net",
    "e4ward.com",
    "einrot.com",
    "fakebox.ml",
    "meltmail.com",
    "mintemail.com",
    "mvrht.com",
    "nowmymail.com",
    "objectmail.com",
    "onewaymail.com",
    "reallymymail.com",
    "receiveblogs.com",
    "sharklasers.com",
    "spamfree24.org",
    "spamfree.eu",
    "spamgob.com",
    "spaml.com",
    "spamspot.com",
    "suremail.info",
    "t-online.hu",
    "teleworm.us",
    "tempe-mail.com",
    "tempr.email",
    "throwam.com",
    "trbvm.com",
    "zetmail.com",
    "zoemail.net",
    # Русские одноразовые домены
    "mailforspam.com",
    "tmailinator.com",
}


class BlockDisposableEmailValidator:
    """
    Проверяет, что email не принадлежит домену одноразовых почт.
    Используется allauth через ACCOUNT_EMAIL_VALIDATORS.
    """

    def validate_email(self, email: str) -> None:
        """allauth вызывает этот метод для каждого email при регистрации."""
        if not email:
            return
        domain = email.lower().split("@")[-1] if "@" in email else ""
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            raise ValidationError(
                "Пожалуйста, используйте настоящий email. "
                "Одноразовые и временные адреса не принимаются.",
                code="disposable_email",
            )
