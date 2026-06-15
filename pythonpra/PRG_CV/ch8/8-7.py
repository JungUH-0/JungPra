from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten,Dense,Dropout,Rescaling
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.applications.densenet import DenseNet121
from tensorflow.keras.utils import image_dataset_from_directory
from tensorflow.keras.callbacks import Callback
import pathlib
from datetime import datetime

# 학습 과정을 자세히 표시하기 위한 커스텀 콜백
class DetailedProgressCallback(Callback):
    def on_train_begin(self, logs=None):
        print("\n" + "="*70)
        print("모델 학습 시작")
        print("="*70)
    
    def on_epoch_begin(self, epoch, logs=None):
        self.epoch_start_time = datetime.now()
        self.batch_count = 0
        print(f'\n[Epoch {epoch + 1}/200] 시작: {self.epoch_start_time.strftime("%H:%M:%S")}')
    
    def on_batch_end(self, batch, logs=None):
        self.batch_count += 1
        # 매 50배치마다 진행 상황 출력
        if self.batch_count % 50 == 0:
            if logs:
                elapsed = (datetime.now() - self.epoch_start_time).total_seconds()
                print(f'  ► 배치 {self.batch_count}: Loss={logs.get("loss", 0):.6f}, '
                      f'Accuracy={logs.get("accuracy", 0):.6f} ({elapsed:.1f}초)')
    
    def on_epoch_end(self, epoch, logs=None):
        epoch_end_time = datetime.now()
        elapsed_time = (epoch_end_time - self.epoch_start_time).total_seconds()
        
        if logs:
            print(f'  ✓ 에포크 완료:')
            print(f'    ├─ 훈련 손실(Loss):        {logs.get("loss", 0):.6f}')
            print(f'    ├─ 훈련 정확도(Accuracy):  {logs.get("accuracy", 0):.6f}')
            print(f'    ├─ 검증 손실(Val_Loss):   {logs.get("val_loss", 0):.6f}')
            print(f'    ├─ 검증 정확도(Val_Acc):  {logs.get("val_accuracy", 0):.6f}')
            print(f'    └─ 총 소요시간:          {elapsed_time:.2f}초')
    
    def on_train_end(self, logs=None):
        print("\n" + "="*70)
        print("모델 학습 완료")
        print("="*70)

data_path=pathlib.Path('datasets/stanford_dogs/images/images')

train_ds=image_dataset_from_directory(data_path,validation_split=0.2,subset='training',seed=123,image_size=(224,224),batch_size=16)
test_ds=image_dataset_from_directory(data_path,validation_split=0.2,subset='validation',seed=123,image_size=(224,224),batch_size=16)

base_model=DenseNet121(weights='imagenet',include_top=False,input_shape=(224,224,3))
cnn=Sequential()
cnn.add(Rescaling(1.0/255.0))
cnn.add(base_model)
cnn.add(Flatten())
cnn.add(Dense(1024,activation='relu'))
cnn.add(Dropout(0.75))
cnn.add(Dense(units=120,activation='softmax'))

cnn.compile(loss='sparse_categorical_crossentropy',optimizer=Adam(learning_rate=0.000001),metrics=['accuracy'])

# 커스텀 콜백과 함께 모델 학습
hist=cnn.fit(train_ds,
             epochs=200,
             validation_data=test_ds,
             verbose=1,
             callbacks=[DetailedProgressCallback()])

print('정확률=',cnn.evaluate(test_ds,verbose=0)[1]*100)

cnn.save('cnn_for_stanford_dogs.h5')	# 미세 조정된 모델을 파일에 저장

import pickle
f=open('dog_species_names.txt','wb')
pickle.dump(train_ds.class_names,f)
f.close()

import matplotlib.pyplot as plt

plt.plot(hist.history['accuracy'])
plt.plot(hist.history['val_accuracy'])
plt.title('Accuracy graph')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train','Validation'])
plt.grid()
plt.show()

plt.plot(hist.history['loss'])
plt.plot(hist.history['val_loss'])
plt.title('Loss graph')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train','Validation'])
plt.grid()
plt.show()