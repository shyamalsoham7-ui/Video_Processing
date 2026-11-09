import os
import uuid
import threading
from flask import Flask, request, render_template, jsonify, send_from_directory
from processor import process_video

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

tasks = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    task_id = str(uuid.uuid4())
    filename = f"{task_id}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    tasks[task_id] = {'status': 'processing', 'progress': 0, 'results': {}}
    
    thread = threading.Thread(target=run_processing, args=(task_id, filepath))
    thread.start()
    
    return jsonify({'task_id': task_id})

def run_processing(task_id, filepath):
    try:
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], task_id)
        os.makedirs(output_dir, exist_ok=True)
        
        results = process_video(filepath, output_dir, lambda p: update_progress(task_id, p))
        
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['results'] = results
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)

def update_progress(task_id, progress):
    if task_id in tasks:
        tasks[task_id]['progress'] = progress

@app.route('/status/<task_id>')
def status(task_id):
    if task_id in tasks:
        return jsonify(tasks[task_id])
    return jsonify({'error': 'Task not found'}), 404

@app.route('/download/<task_id>/<path:filename>')
def download(task_id, filename):
    return send_from_directory(os.path.join(app.config['OUTPUT_FOLDER'], task_id), filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
