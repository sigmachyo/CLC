import os
import re
from pathlib import Path

# ==========================================
# Настройки
# ==========================================
PROJECT_DIR = "." 
OUTPUT_DIR = "output"

MAX_CHUNK_SIZE_BYTES = 500 * 1024  # 500 КБ (максимальный вес одного куска для отправки)
MAX_FILE_SIZE_BYTES = 250 * 1024   # 250 КБ (если ОДИН файл весит больше, это точно не твой код, пропускаем)

def anonymize_code(text: str) -> str:
    """Удаляет личные данные и секреты."""
    patterns = {
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+': '[EMAIL_REDACTED]',
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b': '[IP_REDACTED]',
        r'\+?\d{1,3}?[-.\s]?\(?\d{2,4}?\)?[-.\s]?\d{3}[-.\s]?\d{2,4}\b': '[PHONE_REDACTED]',
        r'\b(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16})\b': '[API_KEY_REDACTED]',
        r'(?i)(password|passwd|secret|api_key|token)\s*[:=]\s*["\'][^"\']+["\']': r'\1 = "[SECRET_REDACTED]"'
    }
    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)
    return text

def compress_for_llm(text: str) -> str:
    """Сжимает код, удаляя двойные пустые строки."""
    return re.sub(r'\n\s*\n', '\n', text)

def pack_project_for_ai(directory_path: str, output_folder: str, max_chunk_size: int, max_file_size: int):
    # Агрессивный фильтр мусора и библиотек
    ignore_dirs = {
        # Системное и IDE
        '.git', '__pycache__', '.idea', '.vscode', 'build', 'dist', 
        # Node.js
        'node_modules', '.next', '.nuxt',
        # Python и виртуальные окружения (все возможные вариации)
        'venv', '.venv', 'env', '.env', 'django_env', 'virtualenv', 
        'Lib', 'Scripts', 'Include', 'site-packages', 'tcl', 
        # Специфика фреймворков
        'migrations', 'static', 'media', 'staticfiles', 'public', 'assets',
        output_folder 
    }
    
    ignore_extensions = {
        # Картинки и медиа
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.mp4', '.mp3',
        # Архивы и бинарники
        '.exe', '.pyc', '.zip', '.tar', '.gz', '.pdf', '.dll', '.so', '.dylib',
        # Базы данных и данные
        '.sqlite3', '.db', '.csv', '.xlsx', '.log', '.lock'
    }

    os.makedirs(output_folder, exist_ok=True)
    
    part_number = 1
    current_out_path = os.path.join(output_folder, f"ai_pack_part_{part_number}.txt")
    out_f = open(current_out_path, 'w', encoding='utf-8')
    current_size = 0
    files_processed = 0

    def write_to_file(content: str):
        nonlocal out_f, current_size, part_number, current_out_path
        
        content_bytes = content.encode('utf-8')
        if current_size + len(content_bytes) > max_chunk_size and current_size > 0:
            out_f.close()
            part_number += 1
            current_out_path = os.path.join(output_folder, f"ai_pack_part_{part_number}.txt")
            out_f = open(current_out_path, 'w', encoding='utf-8')
            current_size = 0
            
            out_f.write(f"--- ПРОДОЛЖЕНИЕ КОДА (Часть {part_number}) ---\n\n")
            current_size += len(f"--- ПРОДОЛЖЕНИЕ КОДА (Часть {part_number}) ---\n\n".encode('utf-8'))

        out_f.write(content)
        current_size += len(content_bytes)

    print(f"Начинаю сборку... Отсекаю файлы больше {max_file_size / 1024:.0f} КБ.")
    write_to_file(f"--- НАЧАЛО КОДА ПРОЕКТА (Часть 1) ---\n\n")
    
    for root, dirs, files in os.walk(directory_path):
        # Удаляем игнорируемые папки из обхода
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            ext = Path(file).suffix.lower()
            if ext in ignore_extensions or file in ('package-lock.json', 'poetry.lock'):
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, directory_path)

            # Проверка на размер файла
            try:
                if os.path.getsize(file_path) > max_file_size:
                    print(f"Пропущен (слишком большой): {rel_path}")
                    continue
            except OSError:
                continue # Если файл невозможно прочитать (например, битая ссылка)

            try:
                with open(file_path, 'r', encoding='utf-8') as in_f:
                    content = in_f.read()

                # Сжимаем и очищаем
                compressed = compress_for_llm(content)
                cleaned = anonymize_code(compressed)

                block = f"\n```\n{cleaned.strip()}\n```\n\n"
                write_to_file(block)
                
                print(f"Добавлен: {rel_path}")
                files_processed += 1

            except UnicodeDecodeError:
                pass # Игнорируем не-текстовые файлы, у которых странные расширения
            except Exception as e:
                print(f"Ошибка при чтении {rel_path}: {e}")

    out_f.close()
    print(f"\n==========================================")
    print(f"Готово! Обработано файлов с кодом: {files_processed}")
    print(f"Результат разбит на {part_number} файл(а/ов) в папке: {os.path.abspath(output_folder)}")
    print(f"==========================================")

if __name__ == "__main__":
    pack_project_for_ai(PROJECT_DIR, OUTPUT_DIR, MAX_CHUNK_SIZE_BYTES, MAX_FILE_SIZE_BYTES)