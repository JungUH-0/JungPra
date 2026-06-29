/*
 * SignBridge - C++ OpenCV 카메라 서버 (Windows/Linux 호환)
 * 카메라 캡처 → JPEG 인코딩 → Python으로 소켓 전송
 */

#include <opencv2/opencv.hpp>
#include <iostream>
#include <string>
#include <vector>
#include <chrono>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    typedef int socklen_t;
#else
    #include <sys/socket.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #define closesocket close
#endif

const int    CAMERA_ID    = 0;
const int    CAM_WIDTH    = 640;
const int    CAM_HEIGHT   = 480;
const int    PYTHON_PORT  = 9999;
const char*  PYTHON_HOST  = "127.0.0.1";
const int    JPEG_QUALITY = 70;

class FPSCounter {
    std::chrono::time_point<std::chrono::steady_clock> prev;
    double fps = 0.0;
public:
    FPSCounter() : prev(std::chrono::steady_clock::now()) {}
    double update() {
        auto now = std::chrono::steady_clock::now();
        double dt = std::chrono::duration<double>(now - prev).count();
        prev = now;
        fps = (dt > 0) ? 1.0 / dt : 0.0;
        return fps;
    }
};

bool sendFrame(SOCKET sock, const std::vector<uchar>& data) {
    uint32_t size = htonl((uint32_t)data.size());
    if (send(sock, (char*)&size, 4, 0) != 4) return false;
    size_t total = 0;
    while (total < data.size()) {
        int sent = send(sock, (char*)(data.data() + total), (int)(data.size() - total), 0);
        if (sent <= 0) return false;
        total += sent;
    }
    return true;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  SignBridge - C++ Camera Server (Win)   " << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "OpenCV 버전: " << CV_VERSION << std::endl;

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2,2), &wsaData) != 0) {
        std::cerr << "[ERROR] WSAStartup failed" << std::endl;
        return -1;
    }
#endif

    // 카메라 열기 - Windows DSHOW 백엔드
    cv::VideoCapture cap;
    cap.open(CAMERA_ID + cv::CAP_DSHOW);
    
    if (!cap.isOpened()) {
        cap.open(CAMERA_ID);
    }
    if (!cap.isOpened()) {
        std::cerr << "[ERROR] Cannot open camera" << std::endl;
        return -1;
    }

    cap.set(cv::CAP_PROP_FRAME_WIDTH,  CAM_WIDTH);
    cap.set(cv::CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT);
    std::cout << "[OK] Camera opened!" << std::endl;
    std::cout << "  Resolution: " << (int)cap.get(cv::CAP_PROP_FRAME_WIDTH)
              << "x" << (int)cap.get(cv::CAP_PROP_FRAME_HEIGHT) << std::endl;

    SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET) {
        std::cerr << "[ERROR] Socket failed" << std::endl;
        return -1;
    }

    struct sockaddr_in server;
    server.sin_family = AF_INET;
    server.sin_port = htons(PYTHON_PORT);
    inet_pton(AF_INET, PYTHON_HOST, &server.sin_addr);

    std::cout << "Connecting to Python server(" << PYTHON_HOST << ":" << PYTHON_PORT << ")..." << std::endl;

    if (connect(sock, (struct sockaddr*)&server, sizeof(server)) < 0) {
        std::cerr << "[ERROR] Cannot connect to Python server! Run Python server first." << std::endl;
        closesocket(sock);
        return -1;
    }
    std::cout << "[OK] Connected to Python server!" << std::endl;
    std::cout << "Press Q to quit" << std::endl;
    std::cout << "========================================" << std::endl;

    cv::Mat frame;
    FPSCounter fpsCounter;
    int frameCount = 0;
    std::vector<int> params = {cv::IMWRITE_JPEG_QUALITY, JPEG_QUALITY};

    while (true) {
        if (!cap.read(frame)) break;
        cv::flip(frame, frame, 1);
        frameCount++;

        double fps = fpsCounter.update();
        cv::putText(frame, "FPS: " + std::to_string((int)fps),
                    cv::Point(10, 30), cv::FONT_HERSHEY_SIMPLEX,
                    0.8, cv::Scalar(0, 255, 100), 2);
        cv::putText(frame, "C++ OpenCV",
                    cv::Point(frame.cols - 150, 30),
                    cv::FONT_HERSHEY_SIMPLEX, 0.6,
                    cv::Scalar(0, 200, 255), 2);

        std::vector<uchar> buf;
        cv::imencode(".jpg", frame, buf, params);
        if (!sendFrame(sock, buf)) {
            std::cerr << "[ERROR] Send failed." << std::endl;
            break;
        }

        cv::imshow("SignBridge - C++ Camera", frame);

        if (frameCount % 30 == 0) {
            std::cout << "FPS: " << (int)fps
                      << " | Frames: " << frameCount << "" << std::endl;
        }

        int key = cv::waitKey(1) & 0xFF;
        if (key == 'q' || key == 27) break;
    }

    closesocket(sock);
#ifdef _WIN32
    WSACleanup();
#endif
    cap.release();
    cv::destroyAllWindows();
    std::cout << "Done!" << std::endl;
    return 0;
}
