document.getElementById('addStepBtn').addEventListener('click', () => {
    const selector = document.getElementById('selectorInput').value.trim();
    const description = document.getElementById('descriptionInput').value.trim();

    if (!selector || !description) {
        alert('Заполните оба поля!');
        return;
    }

    fetch('/add_step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selector, description }),
    })
    .then(res => res.json())
    .then(data => updateStepsList(data.steps));
});

function updateStepsList(steps) {
    const stepsList = document.getElementById('stepsList');
    stepsList.innerHTML = '';

    steps.forEach((step, index) => {
        const li = document.createElement('li');
        li.textContent = `Шаг ${index + 1}: ${step.description}`;
        const upBtn = document.createElement('button');
        const downBtn = document.createElement('button');
        const delBtn = document.createElement('button');

        upBtn.textContent = '↑';
        downBtn.textContent = '↓';
        delBtn.textContent = 'Удалить';

        upBtn.addEventListener('click', () => moveStep(index, 'up'));
        downBtn.addEventListener('click', () => moveStep(index, 'down'));
        delBtn.addEventListener('click', () => removeStep(index));

        li.appendChild(upBtn);
        li.appendChild(downBtn);
        li.appendChild(delBtn);
        stepsList.appendChild(li);
    });
}

function moveStep(index, direction) {
    fetch('/move_step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index, direction }),
    })
    .then(res => res.json())
    .then(data => updateStepsList(data.steps));
}

function removeStep(index) {
    fetch('/remove_step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index }),
    })
    .then(res => res.json())
    .then(data => updateStepsList(data.steps));
}

document.getElementById('generateScriptBtn').addEventListener('click', () => {
    fetch('/generate_script')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'interactive-tutorial-extension.zip';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error downloading extension:', error);
            alert('Произошла ошибка при скачивании расширения');
        });
});
