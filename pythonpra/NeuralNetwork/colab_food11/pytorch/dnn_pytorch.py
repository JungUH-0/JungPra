# Google Colab 실행용: Food-11 데이터셋 (Google Drive 업로드 상태)
from google.colab import drive
drive.mount('/content/drive')

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

DATA_DIR = "/content/drive/MyDrive/food11"
IMG_SIZE = 128
BATCH_SIZE = 32
NUM_CLASSES = 11

transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

training_data = datasets.ImageFolder(root=f"{DATA_DIR}/training", transform=transform)
val_data = datasets.ImageFolder(root=f"{DATA_DIR}/validation", transform=transform)
test_data = datasets.ImageFolder(root=f"{DATA_DIR}/evaluation", transform=transform)

train_dataloader = DataLoader(training_data, batch_size=BATCH_SIZE, shuffle=True)
val_dataloader = DataLoader(val_data, batch_size=BATCH_SIZE)
test_dataloader = DataLoader(test_data, batch_size=BATCH_SIZE)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using {device} device")


class DNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(IMG_SIZE * IMG_SIZE * 3, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, NUM_CLASSES),
        )

    def forward(self, x):
        x = self.flatten(x)
        return self.linear_relu_stack(x)


model = DNN().to(device)
print(model)

loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)


def train(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)
        pred = model(X)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        if batch % 50 == 0:
            loss_val, current = loss.item(), (batch + 1) * len(X)
            print(f"loss: {loss_val:>7f}  [{current:>5d}/{size:>5d}]")


def test(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.eval()
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")


epochs = 5
for t in range(epochs):
    print(f"Epoch {t + 1}\n-------------------------------")
    train(train_dataloader, model, loss_fn, optimizer)
    test(val_dataloader, model, loss_fn)

print("Final evaluation on held-out test set:")
test(test_dataloader, model, loss_fn)
print("Done!")
