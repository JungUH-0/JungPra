import os
import cv2
import tensorflow as tf
import numpy as np

def load_tf_dataset(base_dir):
    video_dir = os.path.join(base_dir, "preprocessed_videos")
    classes = sorted(os.listdir(video_dir))
    
    X_data = []
    y_data = []
    
    for label_idx, class_name in enumerate(classes):
        class_path = os.path.join(video_dir, class_name)
        if os.path.isdir(class_path):
            frames_paths = sorted([os.path.join(class_path, f) for f in os.listdir(class_path) if f.endswith('.jpg')])
            
            sequence_frames = []
            for frame_path in frames_paths:
                # 한글 경로 우회 로드
                with open(frame_path, 'rb') as f:
                    file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
                
                img = img.astype(np.float32) / 255.0
                img = np.expand_dims(img, axis=-1) # (224, 224, 1)
                sequence_frames.append(img)
            
            X_data.append(sequence_frames)
            y_data.append(label_idx)
            
    # 🌟 텐서플로 핵심: 텐서플로는 채널(Channel) 위치가 맨 뒤에 유지되는 것을 선호합니다.
    # 최종 결과 Shape: (동영상개수, 프레임수, 세로, 가로, 채널)
    X_data = np.array(X_data, dtype=np.float32)
    y_data = np.array(y_data, dtype=np.int32)
    
    return tf.convert_to_tensor(X_data), tf.convert_to_tensor(y_data)

# 테스트 실행 코드
if __name__ == "__main__":
    X, y = load_tf_dataset(r"D:\JungPra\pythonpra\signlan")
    if len(X) > 0:
        print("🚀 [TensorFlow] 입력 데이터 Shape (Batch, Seq, H, W, Ch):", X.shape)
        print("🚀 [TensorFlow] 정답 라벨:", y[0].numpy())