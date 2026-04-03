from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import json
from .models import ChatRoom, ChatMessage

@login_required
def chat_list_view(request):
    """Отображает список всех доступных комнат чата"""
    rooms = ChatRoom.objects.all().order_by('-created_at')
    
    # Для каждой комнаты считаем кол-во сообщений и последнее сообщение
    rooms_data = []
    for room in rooms:
        last_msg = room.messages.last()
        rooms_data.append({
            'room': room,
            'message_count': room.messages.count(),
            'last_message': last_msg
        })
        
    return render(request, 'chat_list.html', {'rooms_data': rooms_data})

@login_required
def chat_room_view(request, room_id):
    """Окно самого чата"""
    room = get_object_or_404(ChatRoom, id=room_id)
    return render(request, 'chat_room.html', {'room': room})

@login_required
def api_send_message(request, room_id):
    """API для отправки сообщения через AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
            if text:
                room = get_object_or_404(ChatRoom, id=room_id)
                msg = ChatMessage.objects.create(
                    room=room,
                    author=request.user,
                    text=text
                )
                return JsonResponse({'status': 'ok', 'id': msg.id})
            return JsonResponse({'status': 'error', 'message': 'Empty text'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
def api_get_messages(request, room_id):
    """API для получения новых сообщений (Long polling / AJAX polling)"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Можно передавать ?last_id=123 чтобы получать только новые
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0
        
    messages = room.messages.filter(id__gt=last_id).order_by('created_at')[:50]
    
    data = []
    for m in messages:
        data.append({
            'id': m.id,
            'text': m.text,
            'author_id': m.author.id,
            'author_username': m.author.username,
            'created_at': m.created_at.strftime('%H:%M'),
            'is_me': m.author == request.user
        })
        
    return JsonResponse({'messages': data})
