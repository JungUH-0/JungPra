import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PIL import ImageFont, ImageDraw, Image
import sys
import winsound

def putText_korean(frame, text, pos, size=30, color=(0, 255, 0)):
    img_pil = Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', size)
    draw.text(pos, text, font=font, fill=color)
    return cv.cvtColor(np.array(img_pil), cv.COLOR_RGB2BGR)

class VideoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('도로 영상')
        self.setGeometry(750, 100, 920, 940)
        self.video_label = QLabel(self)
        self.video_label.setGeometry(10, 10, 900, 900)
        self.video_label.setStyleSheet('background-color: black;')

    def show_frame(self, frame):
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img).scaled(900, 900, Qt.KeepAspectRatio)
        self.video_label.setPixmap(pixmap)

class TrafficWeak(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('교통약자 보호')
        self.setGeometry(200, 200, 700, 200)

        signButton = QPushButton('표지판 등록', self)
        roadButton = QPushButton('동영상 불러옴', self)
        webcamButton = QPushButton('웹캠 시작', self)
        recognitionButton = QPushButton('인식', self)
        stopButton = QPushButton('정지', self)
        quitButton = QPushButton('나가기', self)
        self.label = QLabel('환영합니다!', self)

        signButton.setGeometry(10, 10, 100, 30)
        roadButton.setGeometry(110, 10, 100, 30)
        webcamButton.setGeometry(210, 10, 100, 30)
        recognitionButton.setGeometry(310, 10, 100, 30)
        stopButton.setGeometry(410, 10, 100, 30)
        quitButton.setGeometry(510, 10, 100, 30)
        self.label.setGeometry(10, 40, 680, 150)
        self.label.setStyleSheet('font-size: 14px;')

        signButton.clicked.connect(self.signFunction)
        roadButton.clicked.connect(self.roadFunction)
        webcamButton.clicked.connect(self.webcamFunction)
        recognitionButton.clicked.connect(self.recognitionFunction)
        stopButton.clicked.connect(self.stopFunction)
        quitButton.clicked.connect(self.quitFunction)

        self.signFiles = [['child.png', '어린이'], ['child3.png', '어린이보호구역'], ['speed30.png', '속도제한 30']]
        self.signImgs = []
        self.template_kp_des = []
        self.cap = None
        self.running = False
        self.frame_count = 0
        self.last_result = None
        self.last_detected = []

        self.sift = cv.SIFT_create()
        self.matcher = cv.DescriptorMatcher_create(cv.DescriptorMatcher_FLANNBASED)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.video_window = VideoWindow()

    def signFunction(self):
        self.signImgs = []
        self.template_kp_des = []
        for fname, label in self.signFiles:
            img = cv.imread(fname)
            if img is None:
                self.label.setText(f'{fname} 파일을 찾을 수 없습니다.')
                return
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            kp, des = self.sift.detectAndCompute(gray, None)
            self.template_kp_des.append((kp, des, gray, label))
            self.signImgs.append(img)
            cv.imshow(fname, img)  # 표지판 등록시 이미지 표시
        self.label.setText(f'표지판 {len(self.signImgs)}개 등록 완료')

    def roadFunction(self):
        if not self.template_kp_des:
            self.label.setText('먼저 표지판을 등록하세요.')
            return
        fname = QFileDialog.getOpenFileName(self, '동영상 파일 읽기', './', 'Video Files (*.mp4 *.avi *.mov)')
        if fname[0] == '':
            return
        if self.cap:
            self.cap.release()
        self.cap = cv.VideoCapture(fname[0])
        if not self.cap.isOpened():
            self.label.setText('파일을 열 수 없습니다.')
            return
        self.label.setText(f'동영상 로드 완료: {fname[0]}')

    def webcamFunction(self):
        if not self.template_kp_des:
            self.label.setText('먼저 표지판을 등록하세요.')
            return
        if self.cap:
            self.cap.release()
        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            self.label.setText('웹캠을 열 수 없습니다.')
            return
        self.label.setText('웹캠 연결 완료. 인식 버튼을 누르세요.')

    def is_valid_quad(self, corners):
        pts = corners.reshape(4, 2)
    
        # 좌표가 화면 안에 있는지 확인
        if np.any(pts < 0) or np.any(pts[:, 0] > 900) or np.any(pts[:, 1] > 900):
            return False
        
        area = cv.contourArea(pts)
        if area < 2000 or area > 30000:  # 더 엄격하게
            return False
        
        hull = cv.convexHull(pts)
        if len(hull) != 4:
            return False
        
        x, y, w, h = cv.boundingRect(pts)
        if w == 0 or h == 0:
            return False
        ratio = w / h
        if ratio < 0.5 or ratio > 2.0:  # 더 엄격하게
            return False
        
        # 박스 4개 꼭짓점이 너무 일직선이면 제거
        hull_area = cv.contourArea(hull)
        if hull_area < area * 0.7:
            return False
        
        return True

    def detect_signs(self, frame):
        # scale 없이 900x900 그대로 사용
        gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_frame = clahe.apply(gray_frame)
        kp_frame, des_frame = self.sift.detectAndCompute(gray_frame, None)

        result = frame.copy()
        detected_labels = []

        if des_frame is None or len(kp_frame) < 2:
            return result, detected_labels

        for (kp_tmpl, des_tmpl, tmpl, label) in self.template_kp_des:
            if des_tmpl is None or len(des_tmpl) < 2:
                continue

            matches = self.matcher.knnMatch(des_tmpl, des_frame, k=2)
            good = [m for m, n in matches if m.distance < 0.75 * n.distance]

            if len(good) < 6:
                continue

            src_pts = np.float32([kp_tmpl[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            H, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
            if H is None or mask is None:
                continue

            inliers = int(mask.sum())
            if inliers < 4 or inliers / len(good) < 0.4:
                continue

            h, w = tmpl.shape
            corners = np.float32([[0,0],[w,0],[w,h],[0,h]]).reshape(-1, 1, 2)
            dst_corners = cv.perspectiveTransform(corners, H)

            if not self.is_valid_quad(dst_corners):
                continue

            result = cv.polylines(result, [np.int32(dst_corners)], True, (0, 255, 0), 3)

            x = int(dst_corners[0][0][0])
            y = max(int(dst_corners[0][0][1]) - 10, 20)
            result = putText_korean(result, label, (x, y), size=30, color=(0, 255, 0))
            detected_labels.append(label)

        return result, detected_labels

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stopFunction()
            self.label.setText('영상이 끝났습니다.')
            return

        frame = cv.resize(frame, (900, 900))
        self.frame_count += 1

        if self.frame_count % 3 == 0:
            result_frame, detected = self.detect_signs(frame)
            self.last_result = result_frame
            self.last_detected = detected
        else:
            result_frame = self.last_result if self.last_result is not None else frame
            detected = self.last_detected

        self.video_window.show_frame(result_frame)

        if detected:
            self.label.setText(f'검출: {", ".join(detected)} 보호구역입니다. 30km로 서행하세요.')
            self.label.setStyleSheet('color: red; font-size: 14px;')
        else:
            self.label.setText('표지판이 없습니다.')
            self.label.setStyleSheet('color: black; font-size: 14px;')

    def recognitionFunction(self):
        if self.cap is None or not self.cap.isOpened():
            self.label.setText('먼저 동영상 또는 웹캠을 연결하세요.')
            return
        self.running = True
        self.frame_count = 0
        self.video_window.show()
        self.timer.start(30)

    def stopFunction(self):
        self.timer.stop()
        self.running = False
        self.label.setText('인식을 정지했습니다.')
        self.label.setStyleSheet('color: black; font-size: 14px;')

    def quitFunction(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        cv.destroyAllWindows()
        self.video_window.close()
        self.close()

app = QApplication(sys.argv)
win = TrafficWeak()
win.show()
app.exec_()