from transformers import AutoImageProcessor, ViTForImageClassification
from PIL import Image
import torch
import matplotlib.pyplot as plt

img = [
    Image.open("ch11/BSDS_242078.jpg"),
    Image.open("ch11/BSDS_361010.jpg"),
    Image.open("ch11/BSDS_376001.jpg"),
]

processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224")
model = ViTForImageClassification.from_pretrained("google/vit-base-patch16-224")

inputs = processor(img, return_tensors="pt")
res = model(**inputs)

for i in range(res.logits.shape[0]):
    plt.imshow(img[i])
    plt.xticks([])
    plt.yticks([])
    plt.show()
    predicted_label = int(torch.argmax(res.logits[i], dim=-1))
    prob = float(
        torch.nn.functional.softmax(res.logits[i], dim=-1)[predicted_label] * 100.0
    )
    print(i, "번째 영상의 1순위 부류: ", model.config.id2label[predicted_label], prob)
