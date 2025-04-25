# app.py
from flask import Flask, Response, send_file, jsonify
from flask_jwt_extended import JWTManager, jwt_required, verify_jwt_in_request
from auth import auth_bp, init_db
from camera_manager import CameraManager
import eventlet
import cv2
import logging
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

# 初始化应用
app = Flask(__name__, static_folder='../frontend/static')
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
    'JWT_ACCESS_TOKEN_EXPIRES': 3600,
    'JWT_TOKEN_LOCATION': ['headers', 'query_string'],
    'JWT_QUERY_STRING_NAME': 'token'# 新增配置
})

# 初始化组件
jwt = JWTManager(app)
CORS(app, supports_credentials=True)
app.register_blueprint(auth_bp)

# 初始化摄像头
try:
    camera_manager = CameraManager()
except Exception as e:
    logging.critical(f"摄像头初始化失败: {str(e)}")
    exit(1)

@app.route('/')
def index():
    return send_file('../frontend/index.html')

@app.route('/video_feed/<int:cam_id>')
@jwt_required()
def video_feed(cam_id):
    try:
        verify_jwt_in_request()
        if cam_id not in camera_manager.cameras:
            return jsonify({"error": "无效的摄像头ID"}), 404

        def generate():
            while True:
                frame = camera_manager.get_frame(cam_id)
                if frame is not None:
                    _, buffer = cv2.imencode('.jpg', frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                eventlet.sleep(0.1)

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    except Exception as e:
        logging.error(f"视频流错误: {str(e)}")
        return jsonify({"error": "视频流获取失败"}), 500

@app.route('/available_cameras')
@jwt_required()
def available_cameras():
    return jsonify({
        "available_cameras": list(camera_manager.cameras.keys()),
        "current_camera": 0
    })

@app.route('/toggle_camera/<int:cam_id>', methods=['POST'])
@jwt_required()
def toggle_camera(cam_id):
    camera_manager.toggle_camera(cam_id)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    with app.app_context():
        init_db()

    # 修复 Eventlet 兼容性
    import eventlet
    eventlet.monkey_patch(
        os=True,
        select=True,
        socket=True,
        thread=True,
        time=True
    )

    from eventlet import wsgi

    # 启动服务
    print("Server running on http://0.0.0.0:5000")
    wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)