from django.shortcuts import render

def donate_page(request):
    """Страница пожертвований"""
    context = {
        'title': 'Пожертвования'
    }
    return render(request, 'donate.html', context)
