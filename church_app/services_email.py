"""
Сервис отправки электронных писем и квитанций о регистрации на события и конференции KCLC
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_conference_registration_email(registration, site_domain="kclc.ru"):
    """
    Отправляет подтверждение регистрации и электронный билет участнику на email
    """
    event = registration.event
    recipient_email = registration.email or (registration.user.email if registration.user else None)
    
    if not recipient_email:
        logger.warning(f"No recipient email for registration {registration.id}")
        return False

    participant_name = registration.get_full_name()
    subject = f"🕊️ Ваш билет на «{event.title}» — Церковь KCLC"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Церковь KCLC <bot.kclc@mail.ru>')

    context = {
        'registration': registration,
        'event': event,
        'participant_name': participant_name,
        'ticket_number': registration.ticket_number,
        'site_domain': site_domain,
        'support_telegram': event.support_telegram or '@krasnkate',
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>{subject}</title>
    </head>
    <body style="margin:0; padding:0; background-color:#faf8f5; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color:#1a1f36;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#faf8f5; padding:30px 10px;">
            <tr>
                <td align="center">
                    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width:600px; background-color:#ffffff; border-radius:24px; overflow:hidden; box-shadow:0 10px 35px rgba(26,31,54,0.08); border:1px solid rgba(26,31,54,0.06);">
                        <!-- Шапка -->
                        <tr>
                            <td style="background:linear-gradient(135deg, #121624 0%, #1a1f36 50%, #252b48 100%); padding:40px 30px; text-align:center; color:#ffffff;">
                                <p style="margin:0 0 10px 0; color:#c9a84c; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:2px;">
                                    Церковь «Христианской Жизни» Красноярск
                                </p>
                                <h1 style="margin:0 0 15px 0; font-size:24px; font-weight:700; line-height:1.3; color:#ffffff;">
                                    {event.title}
                                </h1>
                                <span style="display:inline-block; padding:6px 16px; background-color:rgba(201,168,76,0.2); color:#c9a84c; border:1px solid rgba(201,168,76,0.4); border-radius:20px; font-size:13px; font-weight:600;">
                                    Регистрация успешно принята
                                </span>
                            </td>
                        </tr>

                        <!-- Тело билета -->
                        <tr>
                            <td style="padding:35px 30px;">
                                <p style="font-size:16px; line-height:1.6; margin:0 0 20px 0;">
                                    Здравствуйте, <strong>{participant_name}</strong>!
                                </p>
                                <p style="font-size:14px; line-height:1.6; color:#4a5568; margin:0 0 25px 0;">
                                    Мы рады подтвердить вашу регистрацию на событие. Ниже указаны детали вашего электронного билета и участия.
                                </p>

                                <!-- Карточка билета -->
                                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#fcfbf9; border:2px dashed #c9a84c; border-radius:18px; margin-bottom:25px;">
                                    <tr>
                                        <td style="padding:22px;">
                                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                <tr>
                                                    <td style="padding-bottom:12px;">
                                                        <span style="font-size:11px; text-transform:uppercase; color:#888; font-weight:700; letter-spacing:1px; display:block;">Номер билета</span>
                                                        <strong style="font-size:18px; color:#1a1f36; font-family:monospace; letter-spacing:1px;">{registration.ticket_number}</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding-bottom:12px;">
                                                        <span style="font-size:11px; text-transform:uppercase; color:#888; font-weight:700; letter-spacing:1px; display:block;">Дата и время</span>
                                                        <strong style="font-size:14px; color:#1a1f36;">{event.start_date.strftime('%d.%m.%Y в %H:%M')} (МСК)</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding-bottom:12px;">
                                                        <span style="font-size:11px; text-transform:uppercase; color:#888; font-weight:700; letter-spacing:1px; display:block;">Формат</span>
                                                        <strong style="font-size:14px; color:#1a1f36;">{event.location}</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>
                                                        <span style="font-size:11px; text-transform:uppercase; color:#888; font-weight:700; letter-spacing:1px; display:block;">Статус пожертвования</span>
                                                        <strong style="font-size:14px; color:#27ae60;">{registration.get_payment_status_display()}</strong>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Ссылка в профиль -->
                                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:25px;">
                                    <tr>
                                        <td align="center">
                                            <a href="https://{site_domain}/profile/" style="display:inline-block; padding:14px 32px; background-color:#c9a84c; color:#1a1f36; text-decoration:none; font-weight:700; font-size:14px; border-radius:14px; box-shadow:0 4px 15px rgba(201,168,76,0.35);">
                                                Открыть билет в моем профиле →
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Поддержка -->
                                <div style="background-color:#f0f4f8; padding:18px; border-radius:14px; font-size:13px; color:#475569; line-height:1.5;">
                                    <strong>Есть вопросы по участию или оплате?</strong><br>
                                    Напишите нашему куратору в Telegram: 
                                    <a href="https://t.me/{event.support_telegram.replace('@', '')}" style="color:#229ED9; font-weight:700; text-decoration:none;">
                                        {event.support_telegram}
                                    </a>
                                </div>
                            </td>
                        </tr>

                        <!-- Подвал -->
                        <tr>
                            <td style="background-color:#f7f6f2; padding:20px 30px; text-align:center; font-size:11px; color:#8b8fa8; border-top:1px solid rgba(26,31,54,0.06);">
                                МЕСТНАЯ РЕЛИГИОЗНАЯ ОРГАНИЗАЦИЯ ЦЕРКОВЬ «ХРИСТИАНСКОЙ ЖИЗНИ» Г. КРАСНОЯРСКА<br>
                                <a href="https://{site_domain}" style="color:#c9a84c; text-decoration:none;">kclc.ru</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    plain_text = strip_tags(html_content)

    try:
        msg = EmailMultiAlternatives(subject, plain_text, from_email, [recipient_email])
        msg.attach_alternative(html_content, "text/html")
        
        # Если прикреплен файл чека — прикрепляем к письму для архива администратора/участника
        if registration.payment_receipt:
            try:
                msg.attach_file(registration.payment_receipt.path)
            except Exception as e:
                logger.warning(f"Could not attach payment receipt: {e}")

        msg.send(fail_silently=False)
        logger.info(f"Registration email sent to {recipient_email} for event {event.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send registration email: {e}")
        return False

