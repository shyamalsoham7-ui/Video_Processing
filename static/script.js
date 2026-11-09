document.getElementById('video-input').addEventListener('change', function(e) {
    document.getElementById('file-name').textContent = e.target.files[0] ? e.target.files[0].name : 'No file selected';
});

document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('video-input');
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append('video', fileInput.files[0]);
    document.getElementById('upload-box').classList.add('hidden');
    document.getElementById('progress-section').classList.remove('hidden');

    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const data = await response.json();
        if (data.error) { alert(data.error); location.reload(); return; }
        pollStatus(data.task_id);
    } catch (error) { alert('Upload failed: ' + error); location.reload(); }
});

async function pollStatus(taskId) {
    const interval = setInterval(async () => {
        const response = await fetch(`/status/${taskId}`);
        const data = await response.json();
        const progressBar = document.getElementById('progress-bar');
        const statusText = document.getElementById('status-text');

        if (data.status === 'processing') {
            progressBar.style.width = data.progress + '%';
            statusText.textContent = `Processing: ${data.progress}%`;
        } else if (data.status === 'completed') {
            clearInterval(interval);
            progressBar.style.width = '100%';
            statusText.textContent = 'Extraction Complete';
            displayResults(taskId, data.results);
        } else if (data.status === 'error') {
            clearInterval(interval);
            statusText.textContent = 'Error: ' + data.error;
            statusText.style.color = '#ff4444';
            progressBar.style.background = '#ff4444';
        }
    }, 2000);
}

function displayResults(taskId, results) {
    document.getElementById('progress-section').classList.add('hidden');
    document.getElementById('results-section').classList.remove('hidden');
    const grid = document.getElementById('results-grid');
    grid.innerHTML = '';

    if (results.tracked_video) grid.innerHTML += createCard('Tracked Video', `/download/${taskId}/${results.tracked_video}`);
    if (results.motion_map) grid.innerHTML += createCard('Motion Map', `/download/${taskId}/${results.motion_map}`);
    if (results.summary) grid.innerHTML += createCard('Summary Video', `/download/${taskId}/${results.summary}`);
    
    if (results.scenes) {
        const scenesStr = results.scenes.map((s, i) => `Scene ${i+1}: ${s[0].toFixed(1)}s - ${s[1].toFixed(1)}s`).join('%0A');
        grid.innerHTML += createCard('Scene Boundaries', `data:text/plain;charset=utf-8,${scenesStr}`, true);
    }
    if (results.important_frames) {
        results.important_frames.forEach((frame, i) => {
            grid.innerHTML += createCard(`Keyframe ${i+1}`, `/download/${taskId}/${frame}`);
        });
    }
}
function createCard(title, link, isData = false) {
    const dlAttr = isData ? 'download="scenes.txt"' : 'target="_blank"';
    return `<div class="result-card"><h4>${title}</h4><a href="${link}" ${dlAttr}>[ VIEW/DOWNLOAD ]</a></div>`;
}
