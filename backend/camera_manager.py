# camera_manager.py
import cv2
import logging
import os


class CameraManager:
    MAX_CAMERA_ATTEMPTS = 3

    def __init__(self):
        self.cameras = {}
        self.backend = self.get_backend()
        self.initialize_cameras()
        logging.info(f"可用摄像头列表: {list(self.cameras.keys())}")

    def get_backend(self):
        if os.name == 'nt':
            # Windows 优先使用 DSHOW
            if cv2.videoio_registry.hasBackend(cv2.CAP_DSHOW):
                return cv2.CAP_DSHOW
        # 其他系统使用默认
        return cv2.CAP_ANY

    def initialize_cameras(self):
        try:
            logging.info(f"正在使用 {self.backend} 后端初始化摄像头...")
            # 仅检测前 3 个索引
            for cam_id in [0, 1, 2]:
                if self.test_camera(cam_id):
                    self.cameras[cam_id] = cv2.VideoCapture(cam_id, self.backend)
            if not self.cameras:
                raise RuntimeError("未检测到可用摄像头")
        except Exception as e:
            logging.error(f"摄像头初始化失败: {str(e)}")
            raise

    def test_camera(self, cam_id):
        cap = cv2.VideoCapture(cam_id, self.backend)
        if cap.isOpened():
            logging.info(f"摄像头 {cam_id} 检测成功")
            cap.release()
            return True
        return False

    def get_frame(self, cam_id):
        if cam_id not in self.cameras:
            logging.warning(f"尝试访问未初始化摄像头 {cam_id}")
            return None

        cap = self.cameras[cam_id]
        if not cap.isOpened():
            self.reconnect(cam_id)

        try:
            ret, frame = cap.read()
            if ret:
                return frame
            self.reconnect(cam_id)
            return cap.read()[1] if cap.isOpened() else None
        except Exception as e:
            logging.error(f"摄像头 {cam_id} 读帧失败: {str(e)}")
            self.reconnect(cam_id)
            return None

    def reconnect(self, cam_id):
        logging.info(f"尝试重新连接摄像头 {cam_id}")
        if cam_id in self.cameras:
            self.cameras[cam_id].release()
        cap = cv2.VideoCapture(cam_id, self.backend)
        if cap.isOpened():
            self.cameras[cam_id] = cap
            return True
        return False

    def toggle_camera(self, cam_id):
        if cam_id in self.cameras:
            if self.cameras[cam_id].isOpened():
                self.cameras[cam_id].release()
                del self.cameras[cam_id]
                logging.info(f"摄像头 {cam_id} 已关闭")
            else:
                if self.test_camera(cam_id):
                    self.cameras[cam_id] = cv2.VideoCapture(cam_id, self.backend)
        else:
            if self.test_camera(cam_id):
                self.cameras[cam_id] = cv2.VideoCapture(cam_id, self.backend)

    def __del__(self):
        for cam_id, cap in self.cameras.items():
            try:
                cap.release()
                logging.info(f"摄像头 {cam_id} 资源已释放")
            except Exception as e:
                logging.error(f"释放摄像头 {cam_id} 资源失败: {str(e)}")