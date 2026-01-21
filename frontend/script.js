// frontend/script.js

let currentImageSource = {
    type: null,  
    file: null,
    url: null
};


// ---- UI вкладки ----
function showTab(tabName, btn) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');
    btn.classList.add('active');
}

function appendImageSource(formData) {
    if (currentImageSource.type === 'file') {
        formData.append('file', currentImageSource.file);
    } else if (currentImageSource.type === 'url') {
        formData.append('image_url', currentImageSource.url);
    }
}

// ---- Анализ обложки ----
async function analyze() {
    const file = document.getElementById('fileInput').files[0];
    const url = document.getElementById('urlInput').value.trim();
    if (!file && !url) { alert('Загрузите файл или введите URL'); return; }

    const formData = new FormData(); 
    if (file) {
        formData.append('file', file);
        currentImageSource = { type: 'file', file, url: null };
    } else if (url) {
        formData.append('image_url', url);
        currentImageSource = { type: 'url', file: null, url };
    }

    try {
        const res = await fetch('/api/analyze', { method: 'POST', body: formData });
        const data = await res.json();
        document.getElementById('analysisResults').style.display = 'block';
        if (data.type === "placeholder") {
            document.getElementById('preview').src = '';
            document.getElementById('result').textContent = data.message;
            return;
        }
        document.getElementById('preview').src = `data:image/png;base64,${data.image_base64}`;
        document.getElementById('result').innerHTML = `
            Дизайн: ${data.design}
            Лицо: ${data.face ? "есть" : "нет"} (${data.face_position})
            Сложность: ${data.complexity}
            Контраст: ${data.color_contrast}
            Тёплота: ${data.warm_cold_balance}
            Текстовая плотность: ${data.text_density}
            Негативное пространство: ${data.negative_space}
        `;
    } catch (err) { alert('Ошибка анализа: ' + err.message); }
}

// ---- Фильтры ----
async function applyFilter(mode) {
    if (!currentImageSource.type) {
        alert('Сначала загрузите изображение');
        return;
    }

    const formData = new FormData();
    appendImageSource(formData);
    formData.append('mode', mode);

    const res = await fetch('/api/filter', {
        method: 'POST',
        body: formData
    });

    if (!res.ok) {
        const text = await res.text();
        console.error(text);
        alert('Ошибка фильтра');
        return;
    }

    const data = await res.json();

    if (data.image_base64) {
        const src = `data:image/png;base64,${data.image_base64}`;
        const preview = document.getElementById('preview');
        preview.src = src;
 
        const blob = await (await fetch(src)).blob();
        const file = new File([blob], 'filtered.png', { type: 'image/png' });

        currentImageSource = {
            type: 'file',
            file: file,
            url: null
        };
    }
}


// ---- Цветопипетка ----
async function getColor(x, y) {
    if (!currentFile) { alert('Сначала загрузите изображение'); return; }
    const formData = new FormData();
    appendImageSource(formData);
    formData.append('x', x);
    formData.append('y', y);
    const res = await fetch('/api/get_color', { method: 'POST', body: formData });
    const data = await res.json();
    return data.color;
}

async function replaceColorPoint() {
    if (!currentFile) { alert('Сначала загрузите изображение'); return; }
    const x = parseInt(prompt("X координата"));
    const y = parseInt(prompt("Y координата"));
    const newColor = prompt("Новый цвет RGB, через запятую (R,G,B)");

    const formData = new FormData();
    appendImageSource(formData);
    formData.append('x', x);
    formData.append('y', y);
    formData.append('new_color', newColor);

    const res = await fetch('/api/replace_color', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.image_base64) document.getElementById('preview').src = `data:image/png;base64,${data.image_base64}`;
}





let colorPickerMode = null;  
let selectedTargetColor = null;
let selectedNewColor = null;


function enableColorPicker(mode) {
    colorPickerMode = mode;
    const message = mode === 'target' ? 
        'Выберите цвет ДЛЯ замены - кликните на изображение' :
        'Выберите НОВЫЙ цвет - кликните на изображение';
    
    document.getElementById(mode + 'ColorInfo').innerHTML = message;
    document.getElementById(mode + 'ColorInfo').style.backgroundColor = '#f0f8ff';
}

// Обработка клика по изображению для выбора цвета
document.addEventListener('DOMContentLoaded', () => {
    const preview = document.getElementById('preview');
    if (!preview) return;

    preview.addEventListener('click', async function(e) {
        if (!colorPickerMode || !currentFile) return;

        const rect = preview.getBoundingClientRect();
        const scaleX = preview.naturalWidth / preview.width;
        const scaleY = preview.naturalHeight / preview.height;

        const x = Math.round((e.clientX - rect.left) * scaleX);
        const y = Math.round((e.clientY - rect.top) * scaleY);

        const formData = new FormData();
        appendImageSource(formData);
        formData.append('x', x);
        formData.append('y', y);

        try {
            const res = await fetch('/api/pick_color', { method: 'POST', body: formData });
            const data = await res.json();

            if (data.hex) {
                if (colorPickerMode === 'target') {
                    selectedTargetColor = data;
                    document.getElementById('targetColorPicker').value = data.hex;
                    document.getElementById('targetColorInfo').innerHTML = 
                        `Цвет для замены:<br>HEX: ${data.hex}<br>RGB: ${data.rgb.join(', ')}`;
                    document.getElementById('targetColorInfo').style.background = data.hex;
                } else {
                    selectedNewColor = data;
                    document.getElementById('newColorPicker').value = data.hex;
                    document.getElementById('newColorInfo').innerHTML = 
                        `Новый цвет:<br>HEX: ${data.hex}<br>RGB: ${data.rgb.join(', ')}`;
                    document.getElementById('newColorInfo').style.background = data.hex;
                }
                colorPickerMode = null;
            }
        } catch (error) {
            alert('Ошибка при выборе цвета: ' + error.message);
        }
    });
});

// Применение замены цвета
async function applyColorReplacement() {
    const targetColorHex = document.getElementById('targetColorPicker').value;
    const newColorHex = document.getElementById('newColorPicker').value;
    const tolerance = document.getElementById('toleranceSlider').value;
    
    if (!currentFile) {
        alert('Сначала загрузите изображение');
        return;
    }
    
    const formData = new FormData();
    appendImageSource(formData);
    formData.append('target_hex', targetColorHex);
    formData.append('new_hex', newColorHex);
    formData.append('tolerance', tolerance);
    
    try {
        const response = await fetch('/api/replace_color_advanced', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.image_base64) {
            document.getElementById('preview').src = 
                `data:image/png;base64,${data.image_base64}`; 
            currentFile = await base64ToFile(data.image_base64, 'modified.png');
        }
    } catch (error) {
        alert('Ошибка при замене цвета: ' + error.message);
    }
}

// Вспомогательная функция для конвертации base64 в File
async function base64ToFile(base64, filename) {
    const res = await fetch(`data:image/png;base64,${base64}`);
    const blob = await res.blob();
    return new File([blob], filename, { type: 'image/png' });
}

// Обновление значения чувствительности
document.getElementById('toleranceSlider').addEventListener('input', function() {
    document.getElementById('toleranceValue').textContent = this.value;
});

function toggleColorTools() {
    const tools = document.getElementById('colorTools');
    tools.style.display = tools.style.display === 'none' ? 'block' : 'none';
    colorPickerMode = null;
}



// ---- Поиск похожих обложек ----
async function findSimilar() {
    const file = document.getElementById('similarityFile').files[0];
    const url = document.getElementById('similarityUrl').value.trim();

    if (!file && !url) {
        alert('Выберите файл или вставьте ссылку');
        return;
    }

    const formData = new FormData();
    if (file) formData.append('file', file);
    if (url) formData.append('image_url', url);
    formData.append('top_n', '5');

    const res = await fetch('/api/similarity', { method: 'POST', body: formData });
    const results = await res.json();
    displaySimilarityResults(results);
}


function displaySimilarityResults(results) {
    const container = document.getElementById('similarityResults');
    if (!results || results.length === 0) { container.innerHTML = '<p>Не найдено</p>'; return; }
    container.innerHTML = results.map(item => `
<div class="similarity-item">
<img src="data:image/png;base64,${item.image_base64}" style="width:150px;height:auto">
<h4>${item.title}</h4>
<p>Сходство: ${item.score}</p>
</div>`).join('');
}




// ---- Статистика с графиками ---- 
async function showGenreStats(forceRefresh = false) {
    const url = forceRefresh ? '/api/genre-stats?force_refresh=true' : '/api/genre-stats';
    
    const res = await fetch(url);
    const data = await res.json();
    const container = document.getElementById('statsResults');
    
    let html = `
    <div class="stats-container">
        <div style=" padding: 10px; margin-bottom: 15px; border-radius: 5px;">
            <strong>${data.cache_info}</strong>
            <button class="btn-secondary" onclick="showGenreStats(true)" 
                    style="margin-left: 15px; font-size: 12px;">
                Обновить данные
            </button>
        </div>
        
        <div class="stats-summary"> 
            <ul>
                <li> Всего книг: ${data.total_books}</li>
                <li> "Обложка скоро появится": ${data.placeholders}</li>
                <li> Минималистичные: ${data.minimalistic}</li>
                <li> Сбалансированные: ${data.total_books - data.minimalistic - data.overloaded}</li>
                <li> Перегруженные: ${data.overloaded}</li>
                <li> С лицами: ${data.faces}</li>
                <li> Средний контраст: ${data.avg_color_contrast?.toFixed(2) || 0}</li>
                <li> Средний warm/cold баланс: ${data.avg_warm_cold_balance?.toFixed(2) || 0}</li>
            </ul>
        </div>`;
     
    if (data.plot_base64) {
        html += `
        <div class="stats-plot"> 
            <img src="data:image/png;base64,${data.plot_base64}" style="max-width: 100%; border: 1px solid #ccc;">
        </div>`;
    }
    
    html += `</div>`;
    container.innerHTML = html;
}





// ---- Анализ видео ---- 
function displaySkatingResults(data) {
    const container = document.getElementById("skatingResults");
    container.innerHTML = "";

    if (!data.success) {
        container.innerHTML = `<div class="error">Ошибка анализа: ${data.error}</div>`;
        return;
    }

    const videoInfo = data.video_info;
    const jumps = data.all_jumps || [];
    const shots = data.shots || [];

    container.innerHTML = `
        <div class="video-stats">
            <h4>📊 Статистика видео</h4>
            <div class="stats-grid">
                <div class="stat-item">⏱ Длительность: ${videoInfo.duration} сек</div>
                <div class="stat-item">🎞️ FPS: ${videoInfo.fps}</div>
                <div class="stat-item">🎬 Сцен: ${videoInfo.shots_detected}</div>
                <div class="stat-item">🔄 Прыжков: ${videoInfo.total_jumps}</div>
            </div>
        </div>
        
        <div class="timeline-section">
            <h4>⏰ Временная шкала прыжков</h4>
            <div id="timeline" class="timeline"></div>
        </div>
        
        <div class="jumps-section">
            <h4>🔍 Детали прыжков</h4>
            <div id="jumpList" class="jump-list"></div>
        </div>
        
        <div class="shots-section">
            <h4>🎬 Анализ сцен</h4>
            <div id="shotList" class="shot-list"></div>
        </div>
    `;
 
    renderJumpDetails(data); 
}

function renderJumpDetails(data) {
    const container = document.getElementById("jumpList");
    const jumps = data.all_jumps || [];
    
    if (jumps.length === 0) {
        container.innerHTML = "<p>Прыжки не обнаружены</p>";
        return;
    }
    
    const html = jumps.map(jump => `
        <div class="jump-item">
            <span class="jump-time">⏱ ${jump.absolute_time}s</span>
            <span class="jump-intensity">💥 ${jump.intensity?.toFixed(2) || 'N/A'}</span>
            <span class="jump-method">🎯 ${jump.detection_method || 'combined'}</span>
            ${jump.height_ratio ? `<span class="jump-height">📏 ${jump.height_ratio.toFixed(2)}x</span>` : ''}
        </div>
    `).join('');
    
    container.innerHTML = html;
}


async function analyzeSkatingVideo() {
    const file = document.getElementById('skatingFile').files[0];
    const youtubeUrl = document.getElementById('youtubeUrl').value.trim();
    const useManualJumps = document.getElementById('useManualJumps').checked;

    if (!file && !youtubeUrl) {
        alert('Загрузите видео');
        return;
    }

    const formData = new FormData();

    if (file) formData.append('file', file);
    if (youtubeUrl) formData.append('youtube_url', youtubeUrl);

    if (useManualJumps) {
        const intervals = collectJumpIntervals();

        if (intervals.length === 0) {
            alert('Укажите хотя бы один интервал прыжка');
            return;
        }
 
        formData.append('jump_intervals', JSON.stringify(intervals));
    }

    document.getElementById('skatingLoading').style.display = 'block';

    const res = await fetch('/api/analyze-skating', {
        method: 'POST',
        body: formData
    });

    const data = await res.json();

    document.getElementById('skatingLoading').style.display = 'none';
    document.getElementById('skatingResults').style.display = 'block';

    displaySkatingResults(data);

    if (data.contrastive_analysis) {
        displayContrastiveAnalysis(data.contrastive_analysis);
    }
}



function displayContrastiveAnalysis(contrastiveData) {
    const container = document.getElementById('contrastiveAnalysis');
    const resultsContainer = document.getElementById('contrastiveResults');
    
    if (!contrastiveData || Object.keys(contrastiveData).length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    
    let html = '<div class="contrastive-grid">';
    
    for (const [feature, data] of Object.entries(contrastiveData)) {
        const featureNames = {
            'brightness': 'Яркость',
            'edges': 'Контуры/Резкость',
            'vertical_motion': 'Вертикальное движение'
        };
        
        const featureName = featureNames[feature] || feature;
        const difference = data.difference;
        const jumpMean = data.jump_mean;
        const nonJumpMean = data.non_jump_mean;
        
        html += `
            <div class="contrastive-item">
                <h6>${featureName}</h6>
                <div class="contrastive-values">
                    <div class="value-item">
                        <span class="label">Во время прыжка:</span>
                        <span class="value">${jumpMean.toFixed(4)}</span>
                    </div>
                    <div class="value-item">
                        <span class="label">Без прыжка:</span>
                        <span class="value">${nonJumpMean.toFixed(4)}</span>
                    </div>
                    <div class="value-item highlight">
                        <span class="label">Разница:</span>
                        <span class="value">${difference > 0 ? '+' : ''}${difference.toFixed(4)}</span>
                    </div>
                </div>
                <div class="difference-indicator ${difference > 0 ? 'positive' : 'negative'}">
                    ${difference > 0 ? ' Выше во время прыжка' : ' Ниже во время прыжка'}
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    resultsContainer.innerHTML = html;
}
 


let jumpIntervals = [];

function addJumpInterval() {
    const container = document.getElementById('jumpIntervalsContainer');
    const div = document.createElement('div');
    div.className = 'jump-interval-input';
    div.innerHTML = `
        <input type="text" class="jump-interval" placeholder="80-82">
        <button type="button" onclick="removeJumpInterval(this)">✖️</button>
    `;
    container.appendChild(div);
}

function removeJumpInterval(button) {
    button.parentElement.remove();
}

function collectJumpIntervals() {
    const inputs = document.querySelectorAll('.jump-interval');
    const intervals = [];
    for (let inp of inputs) {
        const val = inp.value.trim();
        if (!val) continue;
        const match = val.match(/^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)/);
        if (match) {
            const start = parseFloat(match[1]);
            const end = parseFloat(match[2]);
            if (start >= 0 && end > start) {
                intervals.push([start, end]);
            }
        }
    }
    return intervals;
}
 

async function analyzeVideo() {
    const fileInput = document.getElementById('videoFile');
    const useManual = document.getElementById('useManualJumps').checked;

    // Проверка использования ручных интервалов
    if (!useManual) {
        alert("⚠️ Включите 'Использовать ручные интервалы', чтобы провести анализ");
        return;
    }

    // Сбор интервалов
    const intervals = collectJumpIntervals();
    if (intervals.length === 0) {
        alert("Добавьте хотя бы один интервал прыжка (например: 75-78)");
        return;
    }

    // Проверка загруженного файла
    if (!fileInput.files[0]) {
        alert("Загрузите видеофайл");
        return;
    }

    // Подготовка данных
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('jump_intervals', JSON.stringify(intervals));

    // Показываем индикатор загрузки
    const loadingDiv = document.getElementById('videoLoading');
    const statsDiv = document.getElementById('jumpStats');
    const framesSection = document.getElementById('jumpFramesSection');
    
    loadingDiv.style.display = 'block';
    statsDiv.innerHTML = '';
    framesSection.style.display = 'none';

    try {
        // Отправка запроса с таймаутом
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1200000); // 2 минуты таймаут
        
        const response = await fetch('/api/analyze-skating', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Скрываем индикатор загрузки
        loadingDiv.style.display = 'none';

        // Отображаем результаты
        displayResults(result);

    } catch (error) {
        // Скрываем индикатор и показываем ошибку
        loadingDiv.style.display = 'none';
        
        if (error.name === 'AbortError') {
            statsDiv.innerHTML = `
                <div class="error-message">
                    <h4>⏰ Время ожидания истекло</h4>
                    <p>Анализ занял слишком много времени. Попробуйте:</p>
                    <ul>
                        <li>Уменьшить количество интервалов</li>
                        <li>Использовать более короткое видео</li>
                        <li>Проверить подключение к интернету</li>
                    </ul>
                </div>
            `;
        } else {
            statsDiv.innerHTML = `
                <div class="error-message">
                    <h4>❌ Ошибка анализа</h4>
                    <p>${error.message}</p>
                </div>
            `;
        }
        
        console.error('Ошибка анализа видео:', error);
    }
}






function validateJumpInterval(intervalStr) {
    const match = intervalStr.match(/^(\d+\.?\d*)-(\d+\.?\d*)$/);
    if (!match) return null;
    
    const start = parseFloat(match[1]);
    const end = parseFloat(match[2]);
    
    if (isNaN(start) || isNaN(end) || start >= end) return null;
    
    return [start, end];
}
 


function displayResults(result) {
    const statsDiv = document.getElementById('jumpStats');
    if (!result.success) {
        statsDiv.innerHTML = `<p style="color:red; padding:15px; border-radius:8px; background:#fee; margin:10px 0;">✖️ Ошибка: ${result.error}</p>`;
        return;
    }

    const intervals = result.manual_jump_intervals;
    const analyses = result.jump_analysis || [];

    statsDiv.innerHTML = `
    <div id="jumpAnalysisList" style="margin-top: 10px;"></div>
    <div id="jumpFramesSection" style="margin-top:30px; padding:20px; background:#f5f5f5; border-radius:10px;">
        <h4 style="color:#667eea; margin:0 0 15px; font-size:16px; text-align:center;">
            Примеры кадров прыжков
        </h4>
        <div id="jumpFramesContainer" style="display:flex; flex-wrap:wrap; gap:15px; margin-top:15px;"></div>
    </div>
    `;

    const listContainer = document.getElementById('jumpAnalysisList');
    listContainer.innerHTML = analyses.map(analysis => {
        if (analysis.error) {
            return `
            <div style="background:#2a1a1a; padding:15px; margin:15px 0; border-radius:8px; border-left:4px solid #c33;">
                <strong style="color:#f44336;">Прыжок ${analysis.jump_index} — ошибка:</strong> 
                <span style="color:#ccc;">${analysis.error}</span>
            </div>
            `;
        }

        const comp = analysis.comparison;
         
        const allowedMetrics = [
            "Яркость",
            "Контраст (Sobel)",
            "Цветовая энтропия",
            "Макс. высота",
            "Соотношение ширина/высота",
            "Стабильность"
        ];
 
        const metrics = allowedMetrics
            .map(name => Object.values(comp).find(m => m.name === name))
            .filter(Boolean);


        return `
        <div style="background:#252525; padding:20px; margin:20px 0; border-radius:10px; border-left:4px solid #667eea; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            <h5 style="color:#e0e0e0; margin-bottom:15px; font-size:1.2em;">
                Прыжок ${analysis.jump_index}: ${analysis.time_interval[0]}–${analysis.time_interval[1]} с 
                <span style="color:#888; font-size:0.9em;">(длительность: ${analysis.jump_duration} с)</span>
            </h5>
 
            <table style="width:100%; border-collapse: collapse; margin:15px 0; font-size:14px; background:#1e1e1e; border-radius:8px; overflow:hidden;">
            <thead>
                <tr style="background:linear-gradient(90deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2));">
                    <th style="padding:12px; border-bottom:1px solid #333; text-align:left; color:#667eea; font-weight:600;">
                        Метрика
                    </th>
                    <th style="padding:12px; border-bottom:1px solid #333; text-align:center; color:#667eea; font-weight:600;">
                        Подготовка
                    </th>
                    <th style="padding:12px; border-bottom:1px solid #333; text-align:center; color:#667eea; font-weight:600;">
                        Прыжок
                    </th>
                    <th style="padding:12px; border-bottom:1px solid #333; text-align:center; color:#667eea; font-weight:600;">
                        Приземление
                    </th>
                </tr>
            </thead>

                <tbody>
                    ${metrics.map(metric => `
                        <tr style="border-bottom:1px solid #2a2a2a;">
                            <td style="padding:10px 12px; color:#e0e0e0;">
                                ${metric.name}
                            </td>
                            <td style="padding:10px 12px; text-align:center; color:#ccc;">
                                ${metric.pre}
                            </td>
                            <td style="padding:10px 12px; text-align:center; color:#fff; font-weight:bold;">
                                ${metric.jump}
                            </td>
                            <td style="padding:10px 12px; text-align:center; color:#ccc;">
                                ${metric.post}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>

            </table>
 
        </div>
        `;
    }).join('');

    // Отображение кадров
    const framesContainer = document.getElementById('jumpFramesContainer');
    framesContainer.innerHTML = '';

    analyses.forEach(analysis => {
        if (!analysis.sample_frames || analysis.sample_frames.length === 0) return;

        const jumpDiv = document.createElement('div');
        jumpDiv.style.border = '1px solid ';
        jumpDiv.style.borderRadius = '8px';
        jumpDiv.style.padding = '12px';
        jumpDiv.style.marginRight = '25px';
        jumpDiv.style.minWidth = '260px';
        jumpDiv.style.textAlign = 'center';
        jumpDiv.style.cursor = 'pointer';
        jumpDiv.title = 'Кликните для увеличения';

        jumpDiv.onclick = () => {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background: rgba(0,0,0,0.9);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                padding: 20px;
            `;
            modal.innerHTML = `
                <div style="position: absolute; top: 20px; right: 20px; font-size: 24px; cursor: pointer;">✖</div>
                <h3 style="color: white; margin-bottom: 20px;">Прыжок ${analysis.jump_index} — кадры</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; max-width: 90vw;">
                    ${analysis.sample_frames.map(frameBase64 => `
                        <img src="data:image/png;base64,${frameBase64}" style="width: 400px; height: auto; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                    `).join('')}
                </div>
            `;
            modal.querySelector('div').onclick = () => document.body.removeChild(modal);
            document.body.appendChild(modal);
        };

        jumpDiv.innerHTML = `
            <h6 style="margin:0 0 10px; color: #333; font-size:16px;">Прыжок ${analysis.jump_index}</h6>
            ${analysis.sample_frames.map(frameBase64 => `
                <img src="data:image/png;base64,${frameBase64}" style="width: 440px; height: auto; border-radius: 6px; margin: 6px 0; border: 1px solid #eee;">
            `).join('')}
        `;
        framesContainer.appendChild(jumpDiv);
    });
}

