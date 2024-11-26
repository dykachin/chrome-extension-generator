from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import json
import os
import zipfile
from io import BytesIO
from werkzeug.utils import secure_filename
import uuid
from functools import wraps
import re
import shutil

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.secret_key = 'your-secret-key-here'  # Замените на случайный ключ

# Создаем папки для хранения данных
USERS_DATA_DIR = 'users_data'
TEMPLATES_BASE_DIR = 'templates'
os.makedirs(USERS_DATA_DIR, exist_ok=True)
os.makedirs(TEMPLATES_BASE_DIR, exist_ok=True)

def get_user_templates_dir(username):
    """Получает путь к папке с темами конкретного пользователя"""
    templates_dir = os.path.normpath(os.path.join(USERS_DATA_DIR, username, 'templates'))
    os.makedirs(templates_dir, exist_ok=True)
    return templates_dir

def get_user_lessons_file(username):
    """Получает путь к файлу с уроками конкретного пользователя"""
    user_dir = os.path.join(USERS_DATA_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, 'lessons.json')

def secure_filename_with_cyrillic(filename):
    """
    Безопасное преобразование имени файла с поддержкой кириллицы
    """
    # Заменяем все символы кроме букв, цифр и некоторых знаков на underscore
    filename = re.sub(r'[^\w\s-]', '_', filename)
    # Убираем пробелы
    filename = re.sub(r'\s+', '_', filename)
    return filename.strip('._')

def load_users():
    """Загружает список пользователей"""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    """Сохраняет список пользователей"""
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_user_lessons(username):
    """Загружает уроки конкретного пользователя"""
    lessons_file = get_user_lessons_file(username)
    if os.path.exists(lessons_file):
        with open(lessons_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_lessons(username, lessons_data):
    """Сохраняет уроки конкретного пользователя"""
    lessons_file = get_user_lessons_file(username)
    with open(lessons_file, 'w', encoding='utf-8') as f:
        json.dump(lessons_data, f, ensure_ascii=False, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_lessons():
    """Получает уроки текущего пользователя"""
    if 'username' not in session:
        return {}
    return load_user_lessons(session['username'])

def is_safe_path(base_path, path_to_check):
    """Проверяет, что путь находится внутри базовой директории"""
    try:
        # Нормализуем пути для Windows
        base_path = os.path.normpath(os.path.abspath(base_path)).rstrip(os.sep)
        path_to_check = os.path.normpath(os.path.abspath(path_to_check))
        
        print(f"Base path: {base_path}")
        print(f"Check path: {path_to_check}")
        
        # Проверяем, что путь начинается с базового пути
        return path_to_check.startswith(base_path)
    except Exception as e:
        print(f"Error in is_safe_path: {str(e)}")
        return False

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({'status': 'error', 'message': 'Логин не может быть пустым'}), 400
        
    # Очищаем логин от специальных символов
    username = secure_filename_with_cyrillic(username)
    
    # Проверяем, не занят ли логин
    users = load_users()
    if username in users:
        return jsonify({'status': 'error', 'message': 'Этот логин уже занят'}), 400
        
    # Регистрируем пользователя
    users[username] = {
        'created_at': str(uuid.uuid4())  # Можно добавить другие поля при необходимости
    }
    save_users(users)
    
    # Создаем файл для уроков пользователя
    save_user_lessons(username, {})
    
    return jsonify({'status': 'success'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({'status': 'error', 'message': 'Логин не может быть пустым'}), 400
            
        # Очищаем логин от специальных символов
        username = secure_filename_with_cyrillic(username)
        
        # Проверяем существование пользователя
        users = load_users()
        if username not in users:
            return jsonify({'status': 'error', 'message': 'Пользователь не найден'}), 404
            
        session['username'] = username
        
        # Создаем файл для уроков пользователя, если его нет
        if not os.path.exists(get_user_lessons_file(username)):
            save_user_lessons(username, {})
            
        return jsonify({'status': 'success'})
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    lessons = get_current_user_lessons()
    return render_template('index.html', lessons=lessons, username=session['username'])

@app.route('/add_lesson', methods=['POST'])
@login_required
def add_lesson():
    data = request.json
    lesson_name = data.get('name')
    if lesson_name:
        lessons = get_current_user_lessons()
        lessons[lesson_name] = []
        save_user_lessons(session['username'], lessons)  # Сохраняем изменения
    return jsonify({'status': 'success', 'lessons': get_current_user_lessons()})

@app.route('/get_lessons', methods=['GET'])
@login_required
def get_lessons():
    return jsonify({'lessons': get_current_user_lessons()})

@app.route('/add_step', methods=['POST'])
@login_required
def add_step():
    data = request.json
    lesson_name = data.get('lesson')
    if not lesson_name or lesson_name not in get_current_user_lessons():
        return jsonify({'status': 'error', 'message': 'Invalid lesson name'}), 400
        
    step_data = {
        'buttonText': data.get('buttonText'),
        'selector': data.get('selector'),
        'description': data.get('description'),
        'requiresClick': data.get('requiresClick', False)  # По умолчанию False, если не указано
    }
    lessons = get_current_user_lessons()
    lessons[lesson_name].append(step_data)
    save_user_lessons(session['username'], lessons)  # Сохраняем изменения
    return jsonify({'status': 'success', 'steps': lessons[lesson_name]})

@app.route('/get_steps', methods=['GET'])
@login_required
def get_steps():
    lesson_name = request.args.get('lesson')
    if not lesson_name or lesson_name not in get_current_user_lessons():
        return jsonify({'status': 'error', 'message': 'Invalid lesson name'}), 400
    return jsonify({'status': 'success', 'steps': get_current_user_lessons()[lesson_name]})

@app.route('/remove_step', methods=['POST'])
@login_required
def remove_step():
    data = request.json
    lesson_name = data.get('lesson_name')
    index = data.get('index')
    if lesson_name in get_current_user_lessons() and 0 <= index < len(get_current_user_lessons()[lesson_name]):
        lessons = get_current_user_lessons()
        lessons[lesson_name].pop(index)
        save_user_lessons(session['username'], lessons)  # Сохраняем изменения
    return jsonify({'status': 'success', 'steps': get_current_user_lessons()[lesson_name]})

@app.route('/move_step', methods=['POST'])
@login_required
def move_step():
    data = request.json
    lesson_name = data.get('lesson_name')
    index = data.get('index')
    direction = data.get('direction')
    
    if lesson_name not in get_current_user_lessons():
        return jsonify({'status': 'error', 'message': 'Урок не найден'})
        
    lessons = get_current_user_lessons()
    steps = lessons[lesson_name]
    if direction == 'up' and index > 0:
        steps[index], steps[index - 1] = steps[index - 1], steps[index]
    elif direction == 'down' and index < len(steps) - 1:
        steps[index], steps[index + 1] = steps[index + 1], steps[index]
    save_user_lessons(session['username'], lessons)  # Сохраняем изменения
    return jsonify({'status': 'success', 'steps': steps})

@app.route('/delete_lesson', methods=['POST'])
@login_required
def delete_lesson():
    data = request.json
    lesson_name = data.get('lesson_name')
    if lesson_name in get_current_user_lessons():
        lessons = get_current_user_lessons()
        del lessons[lesson_name]
        save_user_lessons(session['username'], lessons)  # Сохраняем изменения
    return jsonify({'status': 'success', 'lessons': get_current_user_lessons()})

@app.route('/edit_step', methods=['POST'])
@login_required
def edit_step():
    data = request.json
    lesson_name = data.get('lesson_name')
    index = data.get('index')
    
    if not lesson_name or lesson_name not in get_current_user_lessons():
        return jsonify({'status': 'error', 'message': 'Урок не найден'}), 400
        
    if index < 0 or index >= len(get_current_user_lessons()[lesson_name]):
        return jsonify({'status': 'error', 'message': 'Шаг не найден'}), 400
        
    step = {
        'buttonText': data.get('buttonText'),
        'selector': data.get('selector'),
        'description': data.get('description'),
        'requiresClick': data.get('requiresClick', False)
    }
    
    lessons = get_current_user_lessons()
    lessons[lesson_name][index] = step
    save_user_lessons(session['username'], lessons)  # Сохраняем изменения
    return jsonify({'status': 'success', 'steps': lessons[lesson_name]})

@app.route('/generate_extension', methods=['GET'])
@login_required
def generate_extension():
    try:
        # Проверяем наличие уроков
        lessons = get_current_user_lessons()
        if not lessons:
            return jsonify({'status': 'error', 'message': 'Добавьте хотя бы один урок перед генерацией расширения'}), 400

        # Создаем ZIP-файл для расширения
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            # Создаем manifest.json
            manifest = {
                "manifest_version": 3,
                "name": "Lesson Helper Extension",
                "version": "1.0",
                "description": "Extension for interactive lessons",
                "permissions": [
                    "activeTab",
                    "scripting",
                    "notifications"
                ],
                "action": {
                    "default_popup": "popup.html",
                    "default_icon": {
                        "16": "icons/icon16.png",
                        "48": "icons/icon48.png",
                        "128": "icons/icon128.png"
                    }
                },
                "icons": {
                    "16": "icons/icon16.png",
                    "48": "icons/icon48.png",
                    "128": "icons/icon128.png"
                },
                "content_scripts": [{
                    "matches": ["<all_urls>"],
                    "js": ["content.js"]
                }],
                "background": {
                    "service_worker": "background.js"
                }
            }
            zf.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))

            # Создаем директорию для скриптов уроков
            for lesson_name, steps in lessons.items():
                # Читаем содержимое mainJS.js
                with open('mainJS.js', 'r', encoding='utf-8') as main_js_file:
                    main_js_content = main_js_file.read()
                
                lesson_script = f"""
// Конфигурация шагов урока
let steps = {json.dumps(steps, ensure_ascii=False, indent=4)};

// Основной код обучающего скрипта
{main_js_content}
"""
                zf.writestr(f'lessons/{lesson_name}.js', lesson_script)

            # Создаем popup.html
            popup_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            width: 300px;
            padding: 10px;
            font-family: Arial, sans-serif;
        }
        .search-container {
            margin-bottom: 10px;
            position: relative;
        }
        .search-input {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .search-input:focus {
            outline: none;
            border-color: #4CAF50;
        }
        select {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            background-color: white;
        }
        select:focus {
            outline: none;
            border-color: #4CAF50;
        }
        button {
            width: 100%;
            padding: 8px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .tab-container {
            display: flex;
            margin-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }
        .tab {
            padding: 8px 15px;
            cursor: pointer;
            border: none;
            background: none;
            color: #666;
            font-size: 14px;
            transition: all 0.2s;
        }
        .tab:hover {
            color: #4CAF50;
        }
        .tab.active {
            color: #4CAF50;
            border-bottom: 2px solid #4CAF50;
        }
        .content {
            display: none;
        }
        .content.active {
            display: block;
        }
    </style>
</head>
<body>
    <h3 style="margin-top: 0; color: #333;">Выберите урок:</h3>
    
    <div class="tab-container">
        <button class="tab active" data-tab="search">Поиск</button>
        <button class="tab" data-tab="select">Список</button>
    </div>

    <div id="searchContent" class="content active">
        <div class="search-container">
            <input type="text" class="search-input" placeholder="Введите название урока..." id="searchInput">
        </div>
        <select id="searchResults" size="6" style="display: none;">
            <!-- Результаты поиска будут здесь -->
        </select>
    </div>

    <div id="selectContent" class="content">
        <select id="lessonSelect" size="6">
            <option value="">-- Выберите урок --</option>
        </select>
    </div>

    <button id="startLesson" disabled>Начать урок</button>

    <script src="popup.js"></script>
</body>
</html>
"""
            zf.writestr('popup.html', popup_html)

            # Создаем popup.js
            popup_js = """
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const lessonSelect = document.getElementById('lessonSelect');
    const startButton = document.getElementById('startLesson');
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.content');
    
    const lessons = """ + json.dumps(list(lessons.keys()), ensure_ascii=False) + """;
    
    // Заполняем select всеми уроками
    lessons.forEach(lesson => {
        const option = document.createElement('option');
        option.value = lesson;
        option.textContent = lesson;
        lessonSelect.appendChild(option);
    });

    // Обработчик поиска
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase();
        const filteredLessons = lessons.filter(lesson => 
            lesson.toLowerCase().includes(query)
        );

        // Очищаем и заполняем результаты поиска
        searchResults.innerHTML = '';
        filteredLessons.forEach(lesson => {
            const option = document.createElement('option');
            option.value = lesson;
            option.textContent = lesson;
            searchResults.appendChild(option);
        });

        // Показываем/скрываем select с результатами
        searchResults.style.display = query ? 'block' : 'none';
        
        // Если есть результаты, выбираем первый
        if (filteredLessons.length > 0) {
            searchResults.selectedIndex = 0;
            startButton.disabled = false;
        } else {
            startButton.disabled = true;
        }
    });

    // Обработчики выбора урока
    searchResults.addEventListener('change', function() {
        startButton.disabled = !this.value;
    });

    lessonSelect.addEventListener('change', function() {
        startButton.disabled = !this.value;
    });

    // Обработчик вкладок
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Убираем активный класс со всех вкладок и контента
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            // Добавляем активный класс текущей вкладке и соответствующему контенту
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab + 'Content').classList.add('active');
            
            // Сбрасываем состояние кнопки
            const activeSelect = document.querySelector('.content.active select');
            startButton.disabled = !activeSelect.value;
        });
    });

    // Обработчик кнопки старта
    startButton.addEventListener('click', function() {
        const activeSelect = document.querySelector('.content.active select');
        const selectedLesson = activeSelect.value;
        
        if (selectedLesson) {
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                chrome.scripting.executeScript({
                    target: {tabId: tabs[0].id},
                    files: [`lessons/${selectedLesson}.js`]
                });
                window.close();
            });
        }
    });
});
"""
            zf.writestr('popup.js', popup_js)

            # Создаем background.js
            background_js = """
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'LESSON_COMPLETE') {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon128.png',
            title: 'Урок завершен!',
            message: `Поздравляем! Вы завершили урок "${request.lesson}"!`
        });
    }
});
"""
            zf.writestr('background.js', background_js)

            # Создаем content.js
            content_js = """
// Общие функции для всех уроков могут быть добавлены здесь
"""
            zf.writestr('content.js', content_js)

            # Добавляем иконки
            icons = {
                16: """
<svg width="16" height="16" xmlns="http://www.w3.org/2000/svg">
    <rect width="16" height="16" fill="#4CAF50" rx="2"/>
    <text x="8" y="12" font-family="Arial" font-size="12" fill="white" text-anchor="middle">L</text>
</svg>
""",
                48: """
<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
    <rect width="48" height="48" fill="#4CAF50" rx="6"/>
    <text x="24" y="36" font-family="Arial" font-size="36" fill="white" text-anchor="middle">L</text>
</svg>
""",
                128: """
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
    <rect width="128" height="128" fill="#4CAF50" rx="16"/>
    <text x="64" y="96" font-family="Arial" font-size="96" fill="white" text-anchor="middle">L</text>
</svg>
"""
            }

            # Создаем директорию для иконок
            for size, svg in icons.items():
                zf.writestr(f'icons/icon{size}.png', svg.encode())

        # Подготавливаем файл для отправки
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='lesson-extension.zip'
        )
    except Exception as e:
        print(f"Error generating extension: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Ошибка при генерации расширения'}), 500

@app.route('/get_templates', methods=['GET'])
@login_required
def get_templates():
    templates_dir = get_user_templates_dir(session['username'])
    templates = []
    
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                template_path = os.path.normpath(os.path.join(templates_dir, filename))
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        templates.append({
                            'name': os.path.splitext(filename)[0],
                            'path': template_path
                        })
                except Exception as e:
                    print(f"Ошибка при загрузке темы {filename}: {str(e)}")
    
    return jsonify(templates)

@app.route('/save_template', methods=['POST'])
@login_required
def save_template():
    data = request.json
    template_name = data.get('template_name')
    template_data = data.get('template_data')
    
    if not template_name or not template_data:
        return jsonify({'status': 'error', 'message': 'Не указано имя или данные темы'}), 400
        
    template_name = secure_filename_with_cyrillic(template_name)
    templates_dir = get_user_templates_dir(session['username'])
    
    # Создаем директорию для тем, если она не существует
    os.makedirs(templates_dir, exist_ok=True)
    
    template_path = os.path.join(templates_dir, f'{template_name}.json')
    
    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ошибка при сохранении темы: {str(e)}'}), 500

@app.route('/upload_template', methods=['POST'])
@login_required
def upload_template():
    if 'template_file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Файл не найден'}), 400
        
    file = request.files['template_file']
    if not file or not file.filename:
        return jsonify({'status': 'error', 'message': 'Файл не выбран'}), 400
        
    if not file.filename.endswith('.json'):
        return jsonify({'status': 'error', 'message': 'Пожалуйста, загрузите файл JSON'}), 400
    
    try:
        # Читаем данные из файла
        template_data = json.loads(file.read().decode('utf-8'))
        
        # Проверяем структуру данных
        if not isinstance(template_data, dict):
            return jsonify({'status': 'error', 'message': 'Неверный формат файла темы'}), 400
            
        # Сохраняем загруженные уроки для текущего пользователя
        save_user_lessons(session['username'], template_data)
        
        return jsonify({
            'status': 'success',
            'data': template_data
        })
    except json.JSONDecodeError:
        return jsonify({'status': 'error', 'message': 'Неверный формат JSON'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ошибка при загрузке темы: {str(e)}'}), 500

@app.route('/load_template', methods=['POST'])
@login_required
def load_template():
    data = request.json
    template_path = data.get('template_path')
    
    if not template_path:
        return jsonify({'status': 'error', 'message': 'Путь к теме не указан'}), 400
    
    # Заменяем прямые слеши на системные
    template_path = template_path.replace('/', os.sep)
    # Нормализуем путь к файлу
    template_path = os.path.normpath(template_path)
    
    # Проверяем, что путь ведет к теме текущего пользователя
    user_templates_dir = get_user_templates_dir(session['username'])
    
    if not is_safe_path(user_templates_dir, template_path):
        return jsonify({'status': 'error', 'message': 'Доступ запрещен'}), 403
    
    if not os.path.exists(template_path):
        return jsonify({'status': 'error', 'message': 'Тема не найдена'}), 404
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
            
        # Сохраняем загруженные уроки для текущего пользователя
        save_user_lessons(session['username'], template_data)
        return jsonify({'status': 'success', 'data': template_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ошибка при загрузке темы: {str(e)}'}), 500

@app.route('/delete_template', methods=['POST'])
@login_required
def delete_template():
    data = request.json
    template_path = data.get('template_path')
    
    if not template_path:
        return jsonify({'status': 'error', 'message': 'Путь к теме не указан'}), 400
    
    # Заменяем прямые слеши на системные
    template_path = template_path.replace('/', os.sep)
    # Нормализуем путь к файлу
    template_path = os.path.normpath(template_path)
    
    # Проверяем, что путь ведет к теме текущего пользователя
    user_templates_dir = get_user_templates_dir(session['username'])
    print(f"User templates dir: {user_templates_dir}")
    print(f"Template path: {template_path}")
    
    if not is_safe_path(user_templates_dir, template_path):
        return jsonify({'status': 'error', 'message': 'Доступ запрещен'}), 403
    
    if not os.path.exists(template_path):
        return jsonify({'status': 'error', 'message': 'Тема не найдена'}), 404
    
    try:
        os.remove(template_path)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ошибка при удалении темы: {str(e)}'}), 500

@app.route('/download_template', methods=['POST'])
@login_required
def download_template():
    data = request.json
    template_path = data.get('template_path')
    
    if not template_path:
        return jsonify({'status': 'error', 'message': 'Путь к теме не указан'}), 400
        
    # Проверяем, что путь ведет к теме текущего пользователя
    user_templates_dir = get_user_templates_dir(session['username'])
    if not is_safe_path(user_templates_dir, template_path):
        return jsonify({'status': 'error', 'message': 'Доступ запрещен'}), 403
        
    if not os.path.exists(template_path):
        return jsonify({'status': 'error', 'message': 'Тема не найдена'}), 404
        
    try:
        return send_file(
            template_path,
            as_attachment=True,
            download_name=os.path.basename(template_path)
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ошибка при скачивании темы: {str(e)}'}), 500

@app.route('/save_lessons', methods=['POST'])
@login_required
def save_lessons():
    try:
        lessons_data = request.json
        save_user_lessons(session['username'], lessons_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error saving lessons: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Ошибка при сохранении уроков: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
