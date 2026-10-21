"""CGI_색상환_동작방식.docx 의 예시 그림을 만든다. 이 파일과 build_doc.js 가 원본이고, png 와 docx 는 산출물이다.

    D:/JungPra/CGI_MOA/CGI/Scripts/python.exe -I -B docs/_colorwheel/make_figures.py

- 입력 (읽기만): moalocal/moa_app/storage/results 의 10-20 실행 결과 2건과 그 상의 윤곽(_garment.png)
  - 예시 1 res_4a45b5b5b714 (헨리넥) → #4B6134 (밝기 38%)
  - 예시 2 res_5c73cc29b6c8 (줄무늬 유니폼) → #FF89D6 (밝기 100%)
  - 두 건 모두 사용자가 색 변경 팝업에서 고른 색이고, 팝업에 뜬 상의 화소 수(291,700 · 229,689)로 같은 결과임을 확인했다
- 색 바꾸기는 색 변경 팝업(moa_app ColorWheel.jsx)과 같은 계산식을 numpy 로 옮겨 쓴다
  (sRGB D65 ↔ CIE LAB, L = 고른 L + (L - 평균 L), a·b = 고른 값 + 차이의 절반, 경계는 3×3 평균 비율로 섞기).
  결과가 1024×1024 라 팝업과 같은 크기에서 계산한다 (팝업은 긴 변 1200px 넘을 때만 줄임)
- 출력: 이 폴더의 ex1_result · ex1_mask · ex1_recolor · ex2_result · ex2_recolor · wheel (.png, 상의 둘레만 잘라 냄)
"""
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = Path("D:/JungPra/pythonpra/moalocal/moa_app/storage/results")
EXAMPLES = [  # (이름, 결과 번호, 고른 색, 팝업에 뜬 상의 화소 수)
    ("ex1", "res_4a45b5b5b714", (0x4B, 0x61, 0x34), 291700),
    ("ex2", "res_5c73cc29b6c8", (0xFF, 0x89, 0xD6), 229689),
]
WHEEL_PICK = (0xFF, 0x89, 0xD6)  # 색상환 그림에 표시할 색 (예시 2, 밝기 100%)
CROP_PAD = 0.12  # 상의 둘레 자를 때 여유 (상의 상자 크기 대비)


def lin(c):
    v = c / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def gam(c):
    return 255 * np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)


def f_lab(t):
    return np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16 / 116)


def f_inv(t):
    t3 = t ** 3
    return np.where(t3 > 0.008856, t3, (t - 16 / 116) / 7.787)


def rgb2lab(rgb):
    r, g, b = (lin(rgb[..., i].astype(np.float64)) for i in range(3))
    fx = f_lab((0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047)
    fy = f_lab(0.2126 * r + 0.7152 * g + 0.0722 * b)
    fz = f_lab((0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883)
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], -1)


def lab2rgb(lab):
    fy = (lab[..., 0] + 16) / 116
    x = f_inv(fy + lab[..., 1] / 500) * 0.95047
    y = f_inv(fy)
    z = f_inv(fy - lab[..., 2] / 200) * 1.08883
    out = [3.2406 * x - 1.5372 * y - 0.4986 * z, -0.9689 * x + 1.8758 * y + 0.0415 * z, 0.0557 * x - 0.2040 * y + 1.0570 * z]
    return np.stack([gam(np.maximum(0, c)) for c in out], -1)


def to_hex(rgb):
    return "#" + "".join(f"{int(round(min(255, max(0, c)))):02X}" for c in rgb)


def recolor(rgb, mask, target):
    m = mask.astype(np.float32)
    s = cv2.boxFilter(m, -1, (3, 3), normalize=False, borderType=cv2.BORDER_CONSTANT)
    s[0, :] = s[-1, :] = s[:, 0] = s[:, -1] = 0  # 화면 계산과 같이 가장자리 한 줄은 건드리지 않음
    alpha = s / 9.0
    sel = alpha > 0
    lab = rgb2lab(rgb[sel])
    mean = lab[alpha[sel] >= 1 - 1e-6].mean(0)
    lt = rgb2lab(np.array(target, np.float64))
    new = np.empty_like(lab)
    new[:, 0] = np.clip(lt[0] + (lab[:, 0] - mean[0]), 0, 100)
    new[:, 1:] = lt[1:] + (lab[:, 1:] - mean[1:]) * 0.5
    t = alpha[sel][:, None]
    out = rgb.astype(np.float64).copy()
    out[sel] = rgb[sel] * (1 - t) + lab2rgb(new) * t
    return np.clip(np.rint(out), 0, 255).astype(np.uint8), mean, int(sel.sum())


def wheel(size=480, pick=None):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    dx, dy = xx - size / 2, yy - size / 2
    r = size / 2 - 6
    d = np.hypot(dx, dy)
    hue = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
    sat = np.minimum(d / r, 1)
    hsv = np.stack([hue / 2, sat * 255, np.full_like(sat, 255)], -1).astype(np.uint8)  # OpenCV HSV: H 0~180
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    img = np.full((size, size, 3), 255, np.uint8)
    img[d <= r] = rgb[d <= r]
    if pick:
        h, s = pick
        px = int(round(size / 2 + np.cos(np.radians(h)) * s * r))
        py = int(round(size / 2 + np.sin(np.radians(h)) * s * r))
        cv2.circle(img, (px, py), 15, (255, 255, 255), 5, cv2.LINE_AA)
        cv2.circle(img, (px, py), 19, (0, 0, 0), 3, cv2.LINE_AA)
    return img


def rgb_to_hs(rgb):
    hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV_FULL)[0, 0].astype(float)
    return hsv[0] * 360 / 256, hsv[1] / 255


def save(name, rgb):
    cv2.imwrite(str(HERE / f"{name}.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def main():
    for old in HERE.glob("fig_*.png"):  # 이전 예시(F01) 그림
        old.unlink()
    for name, rid, target, popup_pixels in EXAMPLES:
        rgb = cv2.cvtColor(cv2.imread(str(RESULTS / f"{rid}.png")), cv2.COLOR_BGR2RGB)
        mask = cv2.imread(str(RESULTS / f"{rid}_garment.png"), cv2.IMREAD_GRAYSCALE) > 127
        out, mean, pixels = recolor(rgb, mask, target)

        ys, xs = np.nonzero(mask)
        bw, bh = xs.max() - xs.min(), ys.max() - ys.min()
        x0, x1 = max(xs.min() - int(bw * CROP_PAD), 0), min(xs.max() + int(bw * CROP_PAD), rgb.shape[1])
        y0, y1 = max(ys.min() - int(bh * CROP_PAD), 0), min(ys.max() + int(bh * CROP_PAD), rgb.shape[0])
        crop = (slice(y0, y1), slice(x0, x1))

        save(f"{name}_result", rgb[crop])
        save(f"{name}_recolor", out[crop])
        if name == "ex1":
            overlay = rgb.astype(np.float32) * 0.45 + 255 * 0.55  # 상의 밖은 흐리게
            overlay[mask] = rgb[mask]
            edge = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)) > 0
            overlay[edge] = (31, 95, 173)
            save(f"{name}_mask", overlay.astype(np.uint8)[crop])
        lt = rgb2lab(np.array(target, np.float64))[0]
        print(f"{name} {rid}: 상의 화소 {pixels} (팝업 {popup_pixels}, {'같음' if pixels == popup_pixels else '다름'})"
              f" · 평균 L {mean[0]:.1f} · 평균 색 {to_hex(lab2rgb(mean))} · 고른 색 {to_hex(target)} L {lt:.0f}"
              f" · 밝기 차 {lt - mean[0]:.1f} · 자른 범위 x {x0}-{x1} y {y0}-{y1}")
    h, s = rgb_to_hs(WHEEL_PICK)
    save("wheel", wheel(pick=(h, s)))
    print(f"색상환 표시: {to_hex(WHEEL_PICK)} 색상 {h:.0f}° 진하기 {s:.2f}")


if __name__ == "__main__":
    main()
