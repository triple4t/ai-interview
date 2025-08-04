# AI Interview Video Analyzer Setup Guide

This guide will help you set up the AI Interview Video Analyzer that is **integrated into the existing interview system** for real-time behavioral analysis during AI interviews.

## Features

- **Integrated Interview Experience**: Video analysis runs alongside the voice interview
- **Real-time Facial Analysis**: Detects emotions using DeepFace during interviews
- **Eye Contact Tracking**: Monitors gaze direction and eye contact duration
- **Head Pose Estimation**: Tracks head movements and orientation
- **Behavioral Analysis**: Detects nervousness, confusion, and other behavioral indicators
- **WebSocket Streaming**: Real-time video streaming with analysis data
- **Non-intrusive UI**: Analysis panel that doesn't interfere with interview flow

## Prerequisites

- Python 3.8+
- OpenCV
- MediaPipe
- DeepFace
- FastAPI
- WebSocket support

## Installation

### 1. Install Dependencies

```bash
cd voice-assistant/backend
pip install -r requirements.txt
```

### 2. Model Files

Ensure the following model files are present in the `models/` directory:

```
models/
├── yolov3.weights
├── yolov3.cfg
├── coco.names
└── haarcascades/
    ├── haarcascade_eye.xml
    ├── haarcascade_eye_tree_eyeglasses.xml
    └── haarcascade_frontalface_default.xml
```

### 3. Environment Variables

Create a `.env` file in the backend directory:

```env
# Backend Configuration
BACKEND_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:3000"]

# Optional: GPU acceleration (if available)
CUDA_VISIBLE_DEVICES=0
```

## Running the Application

### 1. Start the Backend

```bash
cd voice-assistant/backend
python main.py
```

The backend will start on `http://localhost:8000`

### 2. Start the Frontend

```bash
cd voice-assistant/frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:3000`

### 3. Access the Interview with Video Analysis

1. Navigate to `http://localhost:3000`
2. Sign in or sign up
3. Go through the resume upload process
4. Start an interview at `/interview`
5. **The video analysis will automatically start when the interview begins**

## How It Works

### 1. Integration with Interview System

The video analyzer is **seamlessly integrated** into the existing interview system:

- **Automatic Activation**: Video analysis starts when the interview session begins
- **Real-time Monitoring**: Analyzes behavior during the entire interview
- **Non-intrusive Display**: Analysis panel appears in top-left corner
- **Collapsible Details**: Users can show/hide detailed analysis metrics

### 2. Video Processing Pipeline

1. **Frame Capture**: OpenCV captures frames from the webcam
2. **Face Detection**: MediaPipe detects facial landmarks
3. **Emotion Analysis**: DeepFace analyzes emotions
4. **Eye Tracking**: Custom algorithms track eye movements and gaze
5. **Head Pose**: Estimates head orientation using facial landmarks
6. **Behavioral Analysis**: Combines multiple signals to detect behavioral patterns

### 3. Analysis Features

#### Emotion Detection
- Uses DeepFace to detect 7 basic emotions
- Tracks emotion changes over time
- Identifies mixed emotions and behavioral states

#### Eye Contact Analysis
- **Camera Contact**: Direct eye contact with camera
- **Screen Contact**: Looking at screen area
- **Gaze Out**: Looking away from camera/screen
- **No Face**: Face not detected

#### Behavioral Indicators
- **Nervousness**: High blink rate, darting eyes, lip compression
- **Confusion**: Sustained head tilt, asymmetrical eyebrows
- **Attention**: Eye contact duration and consistency

### 4. User Interface

#### Interview Analysis Panel
- **Location**: Top-left corner of interview screen
- **Basic Display**: Shows emotion and gaze direction
- **Expandable**: Click "Show Details" for comprehensive metrics
- **Connection Status**: Green/red indicator for analysis status

#### Metrics Displayed
- **Emotion**: Current emotional state
- **Gaze Direction**: Where the user is looking
- **Eye Movement**: Movement patterns
- **Head Pose**: Pitch, yaw, roll angles
- **Eye Contact Duration**: Time spent looking at camera vs. away

## API Endpoints

### WebSocket Endpoint
- `ws://localhost:8000/api/v1/video-analysis/ws` - Real-time video streaming

### HTTP Endpoints
- `GET /api/v1/video-analysis/status` - Get stream status
- `POST /api/v1/video-analysis/start` - Start video stream
- `POST /api/v1/video-analysis/stop` - Stop video stream
- `GET /api/v1/video-analysis/health` - Health check

## Configuration

### Video Processor Settings

Edit `app/utils/video_processor.py` to adjust:

```python
# Gaze thresholds (in degrees)
GAZE_THRESHOLD_CAMERA_DEGREES = 7.0
GAZE_THRESHOLD_SCREEN_DEGREES = 100.0
GAZE_THRESHOLD_GAZE_OUT_DEGREES = 80.0

# Behavioral thresholds
BLINK_RATE_NERVOUS_HIGH = 35
BLINK_RATE_CONFUSION_LOW = 10
HEAD_TILT_CONFUSION_THRESHOLD = 10
```

### Performance Optimization

1. **GPU Acceleration**: Uncomment CUDA lines in `yolo_utils.py`
2. **Frame Rate**: Adjust `time.sleep(0.03)` in video processor
3. **Model Loading**: Models are loaded once at startup

## Troubleshooting

### Common Issues

1. **Camera Not Found**
   - Ensure webcam is not in use by other applications
   - Check camera permissions
   - Try different camera index (0, 1, 2)

2. **Model Loading Errors**
   - Verify model files are in correct locations
   - Check file permissions
   - Ensure sufficient disk space

3. **Performance Issues**
   - Reduce frame rate
   - Lower resolution
   - Use GPU acceleration if available

4. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify backend is running
   - Check browser console for errors

### Debug Mode

Enable debug logging by setting:

```python
# In main.py
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
```

## Security Considerations

1. **Camera Access**: Only request camera access when needed
2. **Data Privacy**: Video data is processed locally, not stored
3. **HTTPS**: Use HTTPS in production for secure WebSocket connections
4. **Authentication**: User authentication required for interview access

## Production Deployment

1. **Environment**: Use production-grade server (Gunicorn + Uvicorn)
2. **SSL**: Configure HTTPS certificates
3. **Load Balancing**: Use reverse proxy (Nginx)
4. **Monitoring**: Add health checks and logging
5. **Scaling**: Consider multiple instances for high load

## Testing

Run the test script to verify installation:

```bash
cd voice-assistant/backend
python test_video_analyzer.py
```

This will test:
- Module imports
- Model file availability
- Camera access
- Video processor functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 