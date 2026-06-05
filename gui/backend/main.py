import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
import sys

from database import Database
from models import MLModel
from monitor import ActivityWatchMonitor
from notifications import WindowsNotification

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

db = Database()
ml_model = MLModel()
monitor = ActivityWatchMonitor(ml_model)
notifier = WindowsNotification(app_name="FocusPilot")

NOTIFY_URL = "http://localhost:5173/notify"
monitor_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global monitor_task
    logger.info("Backend starting...")
    monitor_task = asyncio.create_task(monitor.monitor_loop(notify))
    yield
    logger.info("Backend shutting down...")
    monitor.stop_monitoring()
    if monitor_task:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    text: str


class FeedbackRequest(BaseModel):
    action: str
    category: Optional[str] = None


class NotificationTestRequest(BaseModel):
    title: str
    message: str


async def notify(data: dict):
    """Send notification to frontend and Windows system"""
    title = data.get("title", "FocusPilot")
    message = data.get("message", "")
    
    # Отправить системное уведомление Windows
    notifier.send_notification(title, message)
    
    # Отправить уведомление в веб-фронтенд (если доступен)
    try:
        requests.post(NOTIFY_URL, json=data, timeout=2)
    except Exception as e:
        logger.debug(f"Failed to send web notification: {e}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    aw_status = "available" if monitor.is_available() else "unavailable"
    return {
        "status": "ok",
        "activitywatch": aw_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/plan")
async def set_plan(request: PlanRequest):
    """Set daily plan"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if db.save_plan(today, request.text):
        logger.info(f"Plan saved for {today}")
        return {"status": "ok", "message": "Plan saved"}
    raise HTTPException(status_code=500, detail="Failed to save plan")


@app.get("/plan")
async def get_plan():
    """Get daily plan"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    plan = db.get_plan(today)
    return {"plan": plan or "", "date": today}


@app.get("/current_state")
async def get_current_state():
    """Get current activity state"""
    activity = monitor.get_current_activity()
    stats = monitor.get_stats()
    return {
        "activity": activity,
        "stats": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/stats")
async def get_stats():
    """Get daily statistics"""
    # Получаем статистику из монитора (в памяти), а не из БД
    monitor_stats = monitor.get_stats()
    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "stats": {
            "work_time": monitor_stats.get("work", 0),
            "distraction_time": monitor_stats.get("distraction", 0),
            "communication_time": monitor_stats.get("communication", 0),
            "break_time": monitor_stats.get("break", 0),
            "plan_adherence": 0.0
        }
    }


@app.post("/feedback")
async def post_feedback(request: FeedbackRequest):
    """Log user feedback"""
    if db.add_feedback(event_type="distraction_notification", action=request.action):
        logger.info(f"Feedback recorded: {request.action}")
        return {"status": "ok"}
    raise HTTPException(status_code=500, detail="Failed to save feedback")


@app.post("/train")
async def train_models():
    """Retrain ML models"""
    try:
        training_data = db.get_training_data()
        if not training_data:
            raise HTTPException(status_code=400, detail="No training data available")
        
        if ml_model.train(training_data):
            logger.info("Models trained successfully")
            return {"status": "ok", "message": "Models trained"}
        raise HTTPException(status_code=500, detail="Training failed")
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pause")
async def pause_monitoring(pause: bool):
    """Pause/resume monitoring"""
    if pause:
        monitor.pause_monitoring()
        logger.info("Monitoring paused")
    else:
        monitor.resume_monitoring()
        logger.info("Monitoring resumed")
    return {"status": "ok", "paused": pause}


@app.post("/test_notification")
async def test_notification(request: NotificationTestRequest):
    """Test Windows notification"""
    if notifier.send_notification(request.title, request.message):
        logger.info(f"Test notification sent: {request.title}")
        return {"status": "ok", "message": "Notification sent"}
    raise HTTPException(status_code=500, detail="Failed to send notification")


@app.post("/test_distraction")
async def test_distraction():
    """Test distraction alert notification"""
    if notifier.send_distraction_alert("YouTube", 5.0):
        logger.info("Distraction test notification sent")
        return {"status": "ok", "message": "Distraction alert sent"}
    raise HTTPException(status_code=500, detail="Failed to send notification")


@app.post("/test_motivation")
async def test_motivation():
    """Send motivational message"""
    if notifier.send_motivational_message():
        logger.info("Motivational message sent")
        return {"status": "ok", "message": "Motivation sent"}
    raise HTTPException(status_code=500, detail="Failed to send notification")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FocusPilot backend on http://0.0.0.0:8765")
    uvicorn.run(app, host="0.0.0.0", port=8765)
