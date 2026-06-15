import numpy as np
from keras.datasets import fashion_mnist
from tensorflow.keras.optimizers import Adam
from keras.models import Sequential
from keras.layers import (
    Dense,
    Reshape,
    Flatten,
    Conv2D,
    Conv2DTranspose,
    LeakyReLU,
    Dropout,
    Input,
)
import matplotlib.pyplot as plt

(x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
x_train = x_train[np.isin(y_train, [8])]
x_train = (x_train.astype("float32") / 255.0) * 2.0 - 1.0
x_train = x_train.reshape(-1, 28, 28, 1)  # 명시적으로 채널 추가

zdim = 100


def make_discriminator(in_shape):
    model = Sequential()
    model.add(Input(shape=in_shape))  # Input 레이어 명시적 추가
    model.add(Conv2D(64, (3, 3), padding="same", activation=LeakyReLU(alpha=0.2)))
    model.add(
        Conv2D(
            128, (3, 3), strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.2)
        )
    )
    model.add(
        Conv2D(
            128, (3, 3), strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.2)
        )
    )
    model.add(
        Conv2D(
            256, (3, 3), strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.2)
        )
    )
    model.add(Flatten())
    model.add(Dropout(0.4))
    model.add(Dense(1, activation="sigmoid"))
    model.compile(
        loss="binary_crossentropy",
        optimizer=Adam(learning_rate=0.0002, beta_1=0.5),
        metrics=["accuracy"],
    )
    return model


def make_generator(zdim):
    model = Sequential()
    model.add(Input(shape=(zdim,)))  # Input 레이어 명시적 추가
    model.add(Dense(7 * 7 * 64, activation=LeakyReLU(alpha=0.2)))
    model.add(Reshape((7, 7, 64)))
    model.add(Conv2D(128, (3, 3), padding="same", activation=LeakyReLU(alpha=0.2)))
    model.add(
        Conv2DTranspose(
            128, (4, 4), strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.2)
        )
    )
    model.add(
        Conv2DTranspose(
            128, (4, 4), strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.2)
        )
    )
    model.add(Conv2D(1, (3, 3), padding="same", activation="tanh"))
    return model


def make_gan(G, D):
    D.trainable = False
    model = Sequential()
    model.add(G)
    model.add(D)
    model.compile(
        loss="binary_crossentropy", optimizer=Adam(learning_rate=0.0002, beta_1=0.5)
    )
    return model


def generate_real_samples(dataset, n_samples):
    ix = np.random.randint(0, dataset.shape[0], n_samples)
    x = dataset[ix]
    y = np.ones((n_samples, 1))
    return x, y


def generate_latent_points(zdim, n_samples):
    return np.random.randn(n_samples, zdim)


def generate_fake_samples(G, zdim, n_samples):
    x_input = generate_latent_points(zdim, n_samples)
    x = G.predict(x_input, verbose=0)
    y = np.zeros((n_samples, 1))
    return x, y


def train(G, D, GAN, dataset, zdim, n_epochs=200, batch_siz=128, verbose=0):
    n_batch = int(dataset.shape[0] / batch_siz)

    for epoch in range(n_epochs):
        for b in range(n_batch):
            x_real, y_real = generate_real_samples(dataset, batch_siz // 2)
            d_loss1, _ = D.train_on_batch(x_real, y_real)
            x_fake, y_fake = generate_fake_samples(G, zdim, batch_siz // 2)
            d_loss2, _ = D.train_on_batch(x_fake, y_fake)

            x_gan = generate_latent_points(zdim, batch_siz)
            y_gan = np.ones((batch_siz, 1))
            g_loss = GAN.train_on_batch(x_gan, y_gan)
        if verbose == 1:
            print(
                "E%d: loss D(real)=%.3f, D(fake)%.3f GAN %.3f"
                % (epoch + 1, d_loss1, d_loss2, g_loss)
            )
        if (epoch + 1) % 10 == 0:
            x_fake, y_fake = generate_fake_samples(G, zdim, 12)
            plt.figure(figsize=(20, 2))
            plt.suptitle("epoch " + str(epoch + 1))
            for k in range(12):
                plt.subplot(1, 12, k + 1)
                plt.imshow((x_fake[k] + 1) / 2.0, cmap="gray")
                plt.xticks([])
                plt.yticks([])
            plt.show()


D = make_discriminator((28, 28, 1))
G = make_generator(zdim)
GAN = make_gan(G, D)
train(G, D, GAN, x_train, zdim, verbose=1)
