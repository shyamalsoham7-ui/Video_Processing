# VideoProcessor // NeuralCore

A complete web application to process videos (up to 60 mins), extracting:
- Important Frames
- Scene Boundaries
- Motion Heatmaps
- Human Object Tracking (YOLOv8)
- Video Summary Generation

## Setup & Running Locally

1. **Prerequisites**: Python 3.8+ is required.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Server**:
   ```bash
   python app.py
   ```
4. **Access the Web Interface**:
   Open your browser and navigate to `http://127.0.0.1:5000`

### Note on Large Videos (60 Minutes)
Processing a full 60-minute video for object tracking and motion mapping is highly computationally intensive. For standard local machines (without an NVIDIA GPU), this code skips frames to optimize processing time. If you deploy this to a cloud server, ensure the server has sufficient memory.
