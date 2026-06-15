import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel,
                              QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
                              QFileDialog)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class SchoolZoneDetector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("숙제 4 - School Zone Detector (SIFT)")
        self.setGeometry(100, 100, 1000, 700)

        self.templates = []
        template_paths = [
            os.path.join(BASE_DIR, "child.png"),
            os.path.join(BASE_DIR, "child2.jpg"),
            os.path.join(BASE_DIR, "speed30.jpg")
        ]
        template_labels = ["Children Protect Area(1)", "Children Protect Area(2)", "Children Protect Area(3)"]

        for path, label in zip(template_paths, template_labels):
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                h, w = img.shape
                if max(h, w) > 300:
                    scale = 300 / max(h, w)
                    img = cv2.resize(img, (int(w*scale), int(h*scale)))
                self.templates.append((img, label))
                print(f"[OK] 템플릿 로드: {label} | 크기: {img.shape}")
            else:
                print(f"[WARN] 템플릿 없음: {path}")

        self.sift = cv2.SIFT_create()
        self.bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

        self.template_kp_des = []
        for (tmpl, label) in self.templates:
            kp, des = self.sift.detectAndCompute(tmpl, None)
            print(f"[INFO] {label} 키포인트 수: {len(kp)}")
            self.template_kp_des.append((kp, des, tmpl, label))

        self.cap = None
        self.playing = False
        self.frame_count = 0
        self.last_result = None
        self.last_detected = []

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        self.video_label = QLabel("동영상 파일을 불러오세요")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 500)
        self.video_label.setStyleSheet("background: black; color: white; font-size: 16px;")

        self.status_label = QLabel("상태: 대기")
        self.status_label.setStyleSheet("font-size: 14px; color: blue;")

        self.load_btn = QPushButton("📂 동영상 불러오기")
        self.load_btn.clicked.connect(self.load_video)
        self.load_btn.setStyleSheet("font-size: 14px; padding: 8px;")

        self.play_btn = QPushButton("▶ 재생")
        self.play_btn.clicked.connect(self.play_video)
        self.play_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        self.play_btn.setEnabled(False)

        self.stop_btn = QPushButton("■ 정지")
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        self.stop_btn.setEnabled(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.status_label)
        layout.addLayout(btn_layout)
        central.setLayout(layout)

    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "동영상 파일 선택", BASE_DIR,
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        )
        if not file_path:
            return

        if self.cap:
            self.cap.release()

        self.cap = cv2.VideoCapture(file_path)

        if not self.cap.isOpened():
            self.status_label.setText("상태: 파일 열기 실패!")
            self.status_label.setStyleSheet("font-size: 14px; color: red;")
            return

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        self.timer_interval = int(1000 / fps)

        self.status_label.setText(f"상태: 파일 로드 완료 ({file_path.split('/')[-1]}, {fps:.1f}fps)")
        self.status_label.setStyleSheet("font-size: 14px; color: green;")
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def play_video(self):
        if self.cap is None:
            return
        self.playing = True
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("상태: 재생 중...")
        self.status_label.setStyleSheet("font-size: 14px; color: red;")
        self.timer.start(int(self.timer_interval * 0.5))  # 2배속

    def stop_video(self):
        self.playing = False
        self.timer.stop()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("상태: 정지됨")
        self.status_label.setStyleSheet("font-size: 14px; color: blue;")

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stop_video()
            self.status_label.setText("상태: 재생 완료")
            return

        self.frame_count += 1

        # 3프레임마다 1번만 SIFT 검출
        if self.frame_count % 3 == 0:
            result_frame, detected = self.detect_signs(frame)
            self.last_result = result_frame
            self.last_detected = detected
        else:
            result_frame = self.last_result if self.last_result is not None else frame
            detected = self.last_detected

        rgb = cv2.cvtColor(result_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img).scaled(
            self.video_label.width(), self.video_label.height(), Qt.KeepAspectRatio)
        self.video_label.setPixmap(pixmap)

        if detected:
            self.status_label.setText(f"검출됨 → {', '.join(detected)}")
            self.status_label.setStyleSheet("font-size: 14px; color: red;")
        else:
            self.status_label.setText("상태: 재생 중...")
            self.status_label.setStyleSheet("font-size: 14px; color: green;")

    def is_valid_quad(self, corners):
        pts = corners.reshape(4, 2)

        area = cv2.contourArea(pts)
        if area < 1500 or area > 200000:
            return False

        hull = cv2.convexHull(pts)
        if len(hull) != 4:
            return False

        x, y, w, h = cv2.boundingRect(pts)
        if w == 0 or h == 0:
            return False
        ratio = w / h
        if ratio < 0.3 or ratio > 3.0:
            return False

        return True

    def detect_signs(self, frame):
        scale = 0.5
        small = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        gray_frame = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_frame = clahe.apply(gray_frame)

        kp_frame, des_frame = self.sift.detectAndCompute(gray_frame, None)

        result = frame.copy()
        detected_labels = []

        if des_frame is None or len(kp_frame) < 2:
            return result, detected_labels

        for (kp_tmpl, des_tmpl, tmpl, label) in self.template_kp_des:
            if des_tmpl is None or len(des_tmpl) < 2:
                continue

            matches = self.bf.knnMatch(des_tmpl, des_frame, k=2)

            good = []
            for m_n in matches:
                if len(m_n) == 2:
                    m, n = m_n
                    if m.distance < 0.75 * n.distance:
                        good.append(m)

            MIN_MATCH = 8
            if len(good) < MIN_MATCH:
                continue

            src_pts = np.float32([kp_tmpl[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

            if H is None:
                continue

            inliers = int(mask.sum())
            if inliers < 5 or inliers / len(good) < 0.4:
                continue

            h, w = tmpl.shape
            corners = np.float32([[0,0],[w,0],[w,h],[0,h]]).reshape(-1, 1, 2)
            dst_corners = cv2.perspectiveTransform(corners, H)
            dst_corners_orig = dst_corners / scale

            if not self.is_valid_quad(dst_corners_orig):
                continue

            result = cv2.polylines(result, [np.int32(dst_corners_orig)], True, (0, 255, 0), 3)

            x = int(dst_corners_orig[0][0][0])
            y = max(int(dst_corners_orig[0][0][1]) - 10, 20)
            cv2.putText(result, label, (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            detected_labels.append(label)

        return result, detected_labels

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SchoolZoneDetector()
    window.show()
    sys.exit(app.exec_())