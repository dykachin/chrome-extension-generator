// Конфигурация шагов урока
let steps = [
    {
        "buttonText": "",
        "selector": "#root > div.sc-kIeTtH.cnxSGb > div > div.sc-lmoMRL.iqbrwR > div > div:nth-child(4)",
        "description": "Наведите сюда",
        "requiresClick": false
    },
    {
        "buttonText": "Создать приказ",
        "selector": "",
        "description": "Нажмите сюда",
        "requiresClick": true
    },
    {
        "buttonText": "Кадровые перемещения",
        "selector": "",
        "description": "Нажмите сюда",
        "requiresClick": true
    },
    {
        "buttonText": "",
        "selector": "body > div:nth-child(7) > div > div.react-ui-1kseug1 > div > div > div > div > div.focus-lock-container > div.react-ui-1ftq6k0 > div > div > span > div > div > div > div > span > div.sc-DJfgX.hwyPtT > div > ul > li:nth-child(1) > ul > li:nth-child(1) > div > div > div.sc-BXqHe.cjuJNa",
        "description": "Выберите этот пункт",
        "requiresClick": false
    },
    {
        "buttonText": "",
        "selector": "body > div:nth-child(7) > div > div.react-ui-1kseug1 > div > div > div > div > div.focus-lock-container > div:nth-child(3) > div > div > div > div > div > div > span:nth-child(1) > div > div > span > span > button > div.react-ui-17axm2e",
        "description": "Нажмите сюда",
        "requiresClick": true
    }
];

// Основной код обучающего скрипта
let currentStepIndex = 0;
let descriptionBox = null;
let isDragging = false;
let offsetX, offsetY;
let tutorialInstance = null;

function createDescriptionBox() {
    descriptionBox = document.createElement('div');
    descriptionBox.style.position = 'absolute';
    descriptionBox.style.padding = '15px';
    descriptionBox.style.backgroundColor = '#fff';
    descriptionBox.style.border = '1px solid #ddd';
    descriptionBox.style.borderRadius = '8px';
    descriptionBox.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    descriptionBox.style.zIndex = 10000;
    descriptionBox.style.minWidth = '320px';
    descriptionBox.style.maxWidth = '400px';
    descriptionBox.style.textAlign = 'center';
    descriptionBox.style.display = 'none';
    descriptionBox.style.cursor = 'move';
    descriptionBox.style.userSelect = 'none';
    descriptionBox.style.opacity = '0';
    descriptionBox.style.transform = 'translateY(10px)';
    descriptionBox.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

    descriptionBox.innerHTML = `
        <div style="
            position: relative;
            padding: 8px;
            margin: -15px -15px 15px -15px;
            background: #f8f9fa;
            border-bottom: 1px solid #eee;
            border-radius: 8px 8px 0 0;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: move;
        ">
            <div style="
                width: 40px;
                height: 4px;
                background: #dee2e6;
                border-radius: 2px;
            "></div>
            <button id="closeButton" style="
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                color: #666;
                font-size: 18px;
                cursor: pointer;
                padding: 5px;
                line-height: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 24px;
                height: 24px;
                border-radius: 4px;
                transition: background-color 0.2s;
            ">×</button>
        </div>
        <div style="
            background-color: #fff;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 15px;
            line-height: 1.5;
            color: #333;
            letter-spacing: 0.2px;
        " id="descriptionText"></div>
        <div style="
            display: flex;
            justify-content: center;
            gap: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        " id="buttonContainer">
        </div>
    `;

    document.body.appendChild(descriptionBox);

    // Добавляем обработчик для кнопки закрытия
    const closeButton = descriptionBox.querySelector('#closeButton');
    closeButton.addEventListener('mouseover', () => {
        closeButton.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';
    });
    closeButton.addEventListener('mouseout', () => {
        closeButton.style.backgroundColor = 'transparent';
    });
    closeButton.addEventListener('click', (e) => {
        e.stopPropagation(); // Предотвращаем всплытие события
        resetTutorial();
    });

    // Добавляем подсказку при первом показе
    const firstTimeKey = 'dragHintShown';
    if (!localStorage.getItem(firstTimeKey)) {
        const hint = document.createElement('div');
        hint.style.position = 'absolute';
        hint.style.top = '-40px';
        hint.style.left = '50%';
        hint.style.transform = 'translateX(-50%)';
        hint.style.background = 'rgba(0, 0, 0, 0.8)';
        hint.style.color = 'white';
        hint.style.padding = '8px 12px';
        hint.style.borderRadius = '4px';
        hint.style.fontSize = '12px';
        hint.textContent = 'Окно можно перетаскивать';
        descriptionBox.appendChild(hint);
        
        setTimeout(() => {
            hint.style.display = 'none';
            localStorage.setItem(firstTimeKey, 'true');
        }, 3000);
    }

    descriptionBox.addEventListener('mousedown', startDragging);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDragging);
}

function showDescriptionBox(element, description) {
    const rect = element.getBoundingClientRect();
    
    // Сначала скрываем с анимацией
    if (descriptionBox.style.display === 'block') {
        descriptionBox.style.opacity = '0';
        descriptionBox.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            updateDescriptionBox();
        }, 300);
    } else {
        updateDescriptionBox();
    }

    function updateDescriptionBox() {
        // Показываем временно для измерения высоты
        descriptionBox.style.display = "block";
        descriptionBox.style.opacity = '0';
        descriptionBox.querySelector("#descriptionText").innerText = description;
        
        const descriptionHeight = descriptionBox.offsetHeight;
        const spaceBelow = window.innerHeight - (rect.bottom + 10); // 10px отступ
        const showAbove = spaceBelow < descriptionHeight;
        
        if (showAbove) {
            descriptionBox.style.top = `${rect.top + window.scrollY - descriptionHeight - 10}px`;
        } else {
            descriptionBox.style.top = `${rect.top + window.scrollY + rect.height + 10}px`;
        }
        
        descriptionBox.style.left = `${rect.left + window.scrollX}px`;
        
        // Добавляем небольшую задержку перед показом для плавности
        setTimeout(() => {
            descriptionBox.style.opacity = '1';
            descriptionBox.style.transform = 'translateY(0)';
        }, 50);
    }
}

function findElement(step) {
    let element = null;
    
    // Функция для поиска в документе и его теневых DOM
    const searchInDocument = (doc, searchFn) => {
        // Поиск в основном документе
        let element = searchFn(doc);
        if (element) return element;

        // Поиск в теневых DOM
        const allElements = doc.querySelectorAll('*');
        for (const el of allElements) {
            if (el.shadowRoot) {
                element = searchFn(el.shadowRoot);
                if (element) return element;
            }
        }
        return null;
    };

    // Рекурсивный поиск в iframe
    const searchInIframes = (doc, searchFn) => {
        const iframes = doc.querySelectorAll('iframe');
        for (const iframe of iframes) {
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                
                // Поиск в документе iframe
                const element = searchFn(iframeDoc);
                if (element) return element;

                // Рекурсивный поиск во вложенных iframe
                const nestedElement = searchInIframes(iframeDoc, searchFn);
                if (nestedElement) return nestedElement;
            } catch (e) {
                console.log('Error accessing iframe:', e);
            }
        }
        return null;
    };

    // Функция поиска по селектору
    if (step.selector && step.selector.trim() !== '') {
        const selectorSearch = (doc) => {
            try {
                return doc.querySelector(step.selector);
            } catch (e) {
                console.log('Invalid selector:', step.selector);
                return null;
            }
        };

        // Поиск в основном документе и теневых DOM
        element = searchInDocument(document, selectorSearch);
        
        // Поиск в iframe если не найдено
        if (!element) {
            element = searchInIframes(document, selectorSearch);
        }
    }

    // Поиск по тексту если элемент не найден
    if (!element && step.buttonText && step.buttonText.trim() !== '') {
        const textSearch = (doc) => {
            const elements = doc.querySelectorAll('button, a, [role="button"], span, div, input[type="button"], input[type="submit"]');
            for (const el of elements) {
                const elementText = el.textContent || el.value || '';
                if (elementText.trim() === step.buttonText.trim()) {
                    return el;
                }
            }
            return null;
        };

        // Поиск в основном документе и теневых DOM
        element = searchInDocument(document, textSearch);
        
        // Поиск в iframe если не найдено
        if (!element) {
            element = searchInIframes(document, textSearch);
        }
    }

    return element;
}

function waitForElement(step, maxAttempts = 20) {
    return new Promise((resolve) => {
        let attempts = 0;
        let observer = null;
        const startTime = Date.now();
        const timeout = 10000; // 10 секунд максимальное время ожидания
        
        // Функция проверки видимости элемента
        const isElementVisible = (element) => {
            if (!element) return false;
            const rect = element.getBoundingClientRect();
            const style = window.getComputedStyle(element);
            return rect.width > 0 && 
                   rect.height > 0 && 
                   style.visibility !== 'hidden' && 
                   style.display !== 'none' &&
                   style.opacity !== '0';
        };

        // Настройка наблюдателя за изменениями DOM
        const setupObserver = () => {
            observer = new MutationObserver((mutations) => {
                const element = findElement(step);
                if (element && isElementVisible(element)) {
                    cleanup();
                    resolve(element);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true
            });
        };

        // Очистка ресурсов
        const cleanup = () => {
            if (observer) {
                observer.disconnect();
                observer = null;
            }
        };

        const checkElement = () => {
            attempts++;
            const element = findElement(step);
            
            if (element && isElementVisible(element)) {
                cleanup();
                resolve(element);
            } else if (Date.now() - startTime < timeout && attempts < maxAttempts) {
                // Экспоненциальная задержка с максимумом в 1 секунду
                const delay = Math.min(Math.pow(1.5, attempts) * 100, 1000);
                setTimeout(checkElement, delay);
            } else {
                cleanup();
                console.log(`Element not found after ${attempts} attempts or timeout:`, step);
                resolve(null);
            }
        };
        
        // Запуск поиска и наблюдателя
        setupObserver();
        checkElement();
    });
}

// Кэш для предварительно загруженных элементов
let preloadedElements = new Map();

// Функция для предварительной загрузки элемента
async function preloadNextElement(stepIndex) {
    if (stepIndex < steps.length) {
        const element = await waitForElement(steps[stepIndex]);
        if (element) {
            preloadedElements.set(stepIndex, element);
        }
    }
}

async function goToStep(stepIndex) {
    if (stepIndex < 0 || stepIndex >= steps.length) return;

    // Плавно скрываем текущий элемент
    if (currentStepIndex >= 0) {
        const prevElement = preloadedElements.get(currentStepIndex) || await waitForElement(steps[currentStepIndex]);
        if (prevElement) {
            prevElement.style.transition = 'outline 0.3s ease';
            prevElement.style.outline = '';
        }
    }

    currentStepIndex = stepIndex;
    const step = steps[stepIndex];
    
    // Используем предзагруженный элемент или ждем появления нового
    let element = preloadedElements.get(stepIndex);
    if (!element) {
        element = await waitForElement(step);
    }

    if (element) {
        // Добавляем плавность для подсветки нового элемента
        element.style.transition = 'outline 0.3s ease';
        element.style.outline = '3px solid #39f';
        showDescriptionBox(element, step.description);

        // Очищаем использованный предзагруженный элемент
        preloadedElements.delete(stepIndex);
        
        // Предзагружаем следующий элемент
        preloadNextElement(stepIndex + 1);

        // Если требуется клик, добавляем обработчик
        if (step.requiresClick) {
            const handleClick = () => {
                element.click();
                element.removeEventListener('click', handleClick);
                goToStep(stepIndex + 1);
            };
            element.addEventListener('click', handleClick);
        }

        // Обновляем кнопки в зависимости от текущего шага
        const buttonContainer = document.getElementById("buttonContainer");
        buttonContainer.innerHTML = '';

        // Кнопка "Назад" показывается всегда, кроме первого шага
        if (stepIndex > 0) {
            const prevButton = document.createElement('button');
            prevButton.textContent = 'Назад';
            applyButtonStyle(prevButton);
            prevButton.onclick = () => goToStep(stepIndex - 1);
            buttonContainer.appendChild(prevButton);
        }

        // Для последнего шага
        if (stepIndex === steps.length - 1) {
            const finishButton = document.createElement('button');
            finishButton.textContent = 'Завершить';
            applyButtonStyle(finishButton);
            finishButton.onclick = () => {
                showCompletionBox();
            };
            buttonContainer.appendChild(finishButton);
        } else {
            // Для не последнего шага всегда показываем кнопку "Далее"
            const nextButton = document.createElement('button');
            nextButton.textContent = 'Далее';
            applyButtonStyle(nextButton);
            nextButton.onclick = () => goToStep(stepIndex + 1);
            buttonContainer.appendChild(nextButton);
        }
    } else {
        showMissingElementMessage(stepIndex);
        
        // Все равно показываем кнопки навигации
        const buttonContainer = document.getElementById("buttonContainer");
        buttonContainer.innerHTML = '';
        
        if (stepIndex > 0) {
            const prevButton = document.createElement('button');
            prevButton.textContent = 'Назад';
            applyButtonStyle(prevButton);
            prevButton.onclick = () => goToStep(stepIndex - 1);
            buttonContainer.appendChild(prevButton);
        }
        
        if (stepIndex < steps.length - 1) {
            const nextButton = document.createElement('button');
            nextButton.textContent = 'Далее';
            applyButtonStyle(nextButton);
            nextButton.onclick = () => goToStep(stepIndex + 1);
            buttonContainer.appendChild(nextButton);
        }
    }
}

function showMissingElementMessage(stepIndex) {
    descriptionBox.style.display = 'block';
    descriptionBox.querySelector("#descriptionText").innerText =
        "Элемент не найден. Вернитесь назад или откройте элемент для продолжения.";

    // Обновляем видимость кнопок
    const buttonContainer = document.getElementById("buttonContainer");
    buttonContainer.innerHTML = '';

    const prevButton = document.createElement('button');
    prevButton.textContent = 'Назад';
    prevButton.onclick = () => goToStep(stepIndex - 1);
    buttonContainer.appendChild(prevButton);

    // Проверяем, появляется ли элемент
    const interval = setInterval(() => {
        const element = findElement(steps[stepIndex]);
        if (element) {
            clearInterval(interval);
            goToStep(stepIndex); // Переходим к текущему шагу
        }
    }, 1000);
}

function startDragging(e) {
    isDragging = true;
    offsetX = e.clientX - descriptionBox.offsetLeft;
    offsetY = e.clientY - descriptionBox.offsetTop;
}

function drag(e) {
    if (isDragging) {
        descriptionBox.style.left = `${e.clientX - offsetX}px`;
        descriptionBox.style.top = `${e.clientY - offsetY}px`;
    }
}

function stopDragging() {
    isDragging = false;
}

function initTutorial() {
    if (tutorialInstance) {
        console.log('Tutorial is already running');
        return;
    }
    
    createDescriptionBox();
    tutorialInstance = {
        start: () => goToStep(0),
        stop: () => {
            // Убираем все подсветки
            steps.forEach(step => {
                const el = findElement(step);
                if (el) el.style.outline = '';
            });
            
            // Скрываем окно описания
            if (descriptionBox) {
                descriptionBox.style.display = 'none';
            }
            
            // Сбрасываем индекс
            currentStepIndex = 0;
            
            // Удаляем старый descriptionBox
            if (descriptionBox) {
                document.body.removeChild(descriptionBox);
                descriptionBox = null;
            }
            
            // Очищаем инстанс
            tutorialInstance = null;
        }
    };
    
    tutorialInstance.start();
}

// Функция для очистки состояния
function resetTutorial() {
    if (descriptionBox) {
        // Добавляем анимацию скрытия
        descriptionBox.style.opacity = '0';
        descriptionBox.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            descriptionBox.style.display = 'none';
            currentStepIndex = -1;
            // Очищаем подсветку с последнего элемента
            const elements = document.querySelectorAll('[style*="outline"]');
            elements.forEach(el => el.style.outline = '');
        }, 300);
    }
}

// Функция для показа сообщения о завершении
function showCompletionBox() {
    // Убираем подсветку с последнего элемента
    if (currentStepIndex >= 0) {
        const prevElement = findElement(steps[currentStepIndex]);
        if (prevElement) {
            prevElement.style.outline = '';
        }
    }

    if (descriptionBox) {
        document.getElementById('descriptionText').textContent = 'Обучение завершено!';
        
        const buttonContainer = document.getElementById('buttonContainer');
        buttonContainer.innerHTML = '';
        
        // Кнопка "Закрыть"
        const closeButton = document.createElement('button');
        closeButton.textContent = 'Закрыть';
        applyButtonStyle(closeButton);
        closeButton.onclick = () => {
            resetTutorial();
        };
        
        buttonContainer.appendChild(closeButton);
    }
}

function applyButtonStyle(button) {
    button.style.backgroundColor = '#39f';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.padding = '8px 16px';
    button.style.borderRadius = '2px';
    button.style.cursor = 'pointer';
    button.style.margin = '0 5px';
    button.style.transition = 'background-color 0.2s';
    button.style.fontSize = '14px';
    button.style.fontWeight = '500';

    // Добавляем эффект при наведении
    button.addEventListener('mouseover', () => {
        button.style.backgroundColor = '#1a8cff';
    });
    button.addEventListener('mouseout', () => {
        button.style.backgroundColor = '#39f';
    });
}

initTutorial();
