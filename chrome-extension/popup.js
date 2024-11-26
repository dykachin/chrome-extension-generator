document.addEventListener('DOMContentLoaded', function() {
    loadLessons();
    
    document.getElementById('createLesson').addEventListener('click', createLesson);
    document.getElementById('addStep').addEventListener('click', addStep);
});

let currentLessonId = null;

function createLesson() {
    const title = document.getElementById('lessonTitle').value;
    const theme = document.getElementById('lessonTheme').value;
    
    if (!title || !theme) {
        alert('Пожалуйста, заполните все поля');
        return;
    }
    
    chrome.storage.sync.get(['lessons'], function(result) {
        const lessons = result.lessons || [];
        const newLesson = {
            id: Date.now(),
            title: title,
            theme: theme,
            steps: []
        };
        
        lessons.push(newLesson);
        chrome.storage.sync.set({ lessons: lessons }, function() {
            document.getElementById('lessonTitle').value = '';
            document.getElementById('lessonTheme').value = '';
            loadLessons();
        });
    });
}

function loadLessons() {
    const lessonsList = document.getElementById('lessonsList');
    chrome.storage.sync.get(['lessons'], function(result) {
        const lessons = result.lessons || [];
        let html = '<h2>Мои уроки</h2>';
        
        lessons.forEach(function(lesson) {
            html += `
                <div class="lesson-item">
                    <h3>${lesson.title} - ${lesson.theme}</h3>
                    <button onclick="showStepsForm(${lesson.id}, '${lesson.title}')">Добавить шаг</button>
                    <button class="delete-btn" onclick="deleteLesson(${lesson.id})">Удалить урок</button>
                    <div class="steps-list">
                        ${lesson.steps.map((step, index) => `
                            <div class="step-item">
                                ${index + 1}. ${step}
                                <button class="delete-btn" onclick="deleteStep(${lesson.id}, ${index})">Удалить</button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        });
        
        lessonsList.innerHTML = html;
    });
}

function showStepsForm(lessonId, lessonTitle) {
    currentLessonId = lessonId;
    document.getElementById('currentLessonTitle').textContent = lessonTitle;
    document.getElementById('stepsForm').style.display = 'block';
    document.getElementById('stepDescription').value = '';
}

function addStep() {
    if (!currentLessonId) return;
    
    const stepDescription = document.getElementById('stepDescription').value;
    if (!stepDescription) {
        alert('Пожалуйста, введите описание шага');
        return;
    }
    
    chrome.storage.sync.get(['lessons'], function(result) {
        const lessons = result.lessons || [];
        const lessonIndex = lessons.findIndex(l => l.id === currentLessonId);
        
        if (lessonIndex !== -1) {
            lessons[lessonIndex].steps.push(stepDescription);
            chrome.storage.sync.set({ lessons: lessons }, function() {
                document.getElementById('stepDescription').value = '';
                loadLessons();
            });
        }
    });
}

function deleteLesson(lessonId) {
    if (confirm('Вы уверены, что хотите удалить этот урок?')) {
        chrome.storage.sync.get(['lessons'], function(result) {
            const lessons = result.lessons || [];
            const updatedLessons = lessons.filter(lesson => lesson.id !== lessonId);
            
            chrome.storage.sync.set({ lessons: updatedLessons }, function() {
                loadLessons();
                if (currentLessonId === lessonId) {
                    document.getElementById('stepsForm').style.display = 'none';
                    currentLessonId = null;
                }
            });
        });
    }
}

function deleteStep(lessonId, stepIndex) {
    if (confirm('Вы уверены, что хотите удалить этот шаг?')) {
        chrome.storage.sync.get(['lessons'], function(result) {
            const lessons = result.lessons || [];
            const lessonIndex = lessons.findIndex(l => l.id === lessonId);
            
            if (lessonIndex !== -1) {
                lessons[lessonIndex].steps.splice(stepIndex, 1);
                chrome.storage.sync.set({ lessons: lessons }, function() {
                    loadLessons();
                });
            }
        });
    }
}
