from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Donation

def donate_page(request):
    """Страница пожертвований и форма создания Donation"""
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
            donation = Donation.objects.create(
                user=request.user if request.user.is_authenticated else None,
                amount=amount,
                status='pending'
            )
            return redirect('mock_payment_gateway', payment_id=donation.payment_id)
        except (ValueError, TypeError):
            # В реальном приложении здесь нужен messages.error или форма
            return redirect('donate')

    context = {
        'title': 'Пожертвования'
    }
    return render(request, 'donate.html', context)

def mock_payment_gateway(request, payment_id):
    """Фейковый платежный шлюз (Имитация ЮKassa/CloudPayments)"""
    donation = get_object_or_404(Donation, payment_id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'pay':
            donation.status = 'success'
            donation.save()
            return redirect('donate_success')
        else:
            donation.status = 'failed'
            donation.save()
            return redirect('donate_fail')
            
    context = {
        'title': 'Оплата: Тестовый режим',
        'donation': donation
    }
    return render(request, 'mock_gateway.html', context)

def donate_success(request):
    """Страница успешной оплаты"""
    return render(request, 'donate_success.html', {'title': 'Успешная оплата'})

def donate_fail(request):
    """Страница ошибки"""
    return render(request, 'donate_fail.html', {'title': 'Ошибка оплаты'})
