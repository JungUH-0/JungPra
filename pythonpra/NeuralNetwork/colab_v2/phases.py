# ============================================================
# Food-11 실험 v2 — 학습 루프와 Phase 실행
#
#   common.py를 먼저 실행한 뒤 이 셀을 붙여넣는다.
# ============================================================

import time
import numpy as np
from dataclasses import replace


# ============================================================
# 1. Keras 실행
# ============================================================

def run_keras(cfg, phase=""):
    import keras

    set_all_seeds(cfg.seed)
    train_ds, val_ds, test_ds = keras_data(cfg)
    model = build_keras(cfg)
    # 모델이 logit을 내보내므로 from_logits=True.
    # PyTorch의 nn.CrossEntropyLoss와 같은 계산이 된다.
    model.compile(
        optimizer=keras_optimizer(cfg),
        loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=["accuracy"])

    mode = "max" if cfg.es_monitor == "val_accuracy" else "min"
    cbs = [keras.callbacks.EarlyStopping(
        monitor=cfg.es_monitor, mode=mode, patience=cfg.es_patience,
        restore_best_weights=True)]
    if cfg.lr_sched:
        cbs.append(keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=cfg.lr_sched_factor,
            patience=cfg.lr_sched_patience, min_lr=1e-6, verbose=1))

    t0 = time.time()
    h = model.fit(train_ds, validation_data=val_ds,
                  epochs=cfg.epochs, callbacks=cbs, verbose=2)
    wall = time.time() - t0

    ran = len(h.history["loss"])
    test_loss, test_acc = model.evaluate(test_ds, verbose=0)

    # 클래스별 재현율 — v1에 없던 지표
    y_true, y_pred = [], []
    for x, y in test_ds:
        y_true.append(np.asarray(y))
        y_pred.append(np.argmax(model.predict(x, verbose=0), axis=1))
    recall = per_class_recall(np.concatenate(y_true), np.concatenate(y_pred))

    # 학습률 변화 — ReduceLR 발동 여부가 여기 남는다
    lr_hist = h.history.get("learning_rate") or h.history.get("lr") or []

    return dict(
        phase=phase, cfg_id=cfg.id(), framework="keras",
        n_params=count_keras(model),
        epochs_ran=ran, stopped_by="early" if ran < cfg.epochs else "max_epoch",
        train_acc=h.history["accuracy"][-1], train_loss=h.history["loss"][-1],
        val_acc=h.history["val_accuracy"][-1], val_loss=h.history["val_loss"][-1],
        test_acc=test_acc, test_loss=test_loss,
        per_class_recall=str(recall),
        lr_history=str([round(float(v), 8) for v in lr_hist]),
        wall_sec=round(wall, 1), **asdict(cfg))


# ============================================================
# 2. PyTorch 실행
# ============================================================

def run_torch(cfg, phase=""):
    import copy
    import torch
    from torch import nn

    set_all_seeds(cfg.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    train_dl, val_dl, test_dl = torch_data(cfg)
    model = build_torch(cfg).to(dev)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch_optimizer(cfg, model)

    sched = None
    if cfg.lr_sched:
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
            opt, mode="min", factor=cfg.lr_sched_factor,
            patience=cfg.lr_sched_patience, min_lr=1e-6)

    def evaluate(dl, collect=False):
        model.eval()
        tot, correct, n = 0.0, 0, 0
        yt, yp = [], []
        with torch.no_grad():
            for x, y in dl:
                x, y = x.to(dev), y.to(dev)
                p = model(x)
                tot += loss_fn(p, y).item() * y.size(0)
                pred = p.argmax(1)
                correct += (pred == y).sum().item()
                n += y.size(0)
                if collect:
                    yt.append(y.cpu().numpy()); yp.append(pred.cpu().numpy())
        out = (tot / n, correct / n)
        return out + ((np.concatenate(yt), np.concatenate(yp)),) if collect else out

    better = (lambda a, b: a > b) if cfg.es_monitor == "val_accuracy" else (lambda a, b: a < b)
    best = -np.inf if cfg.es_monitor == "val_accuracy" else np.inf
    best_state, wait, lr_hist = None, 0, []
    tr_acc = tr_loss = va_acc = va_loss = 0.0

    t0 = time.time()
    for ep in range(cfg.epochs):
        model.train()
        tot, correct, n = 0.0, 0, 0
        for x, y in train_dl:
            x, y = x.to(dev), y.to(dev)
            p = model(x)
            loss = loss_fn(p, y)
            loss.backward()
            opt.step()
            opt.zero_grad()
            tot += loss.item() * y.size(0)
            correct += (p.argmax(1) == y).sum().item()
            n += y.size(0)
        tr_loss, tr_acc = tot / n, correct / n
        va_loss, va_acc = evaluate(val_dl)
        if sched:
            sched.step(va_loss)
        lr_hist.append(opt.param_groups[0]["lr"])

        print(f"[{ep+1:>2}] acc {tr_acc:.4f} loss {tr_loss:.4f} | "
              f"val {va_acc:.4f} / {va_loss:.4f} | lr {lr_hist[-1]:.2e}")

        cur = va_acc if cfg.es_monitor == "val_accuracy" else va_loss
        if better(cur, best):
            best, wait = cur, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            wait += 1
            if wait >= cfg.es_patience:
                print(f"Early stopping at epoch {ep+1}")
                break
    wall = time.time() - t0
    ran = ep + 1

    model.load_state_dict(best_state)
    test_loss, test_acc, (yt, yp) = evaluate(test_dl, collect=True)

    return dict(
        phase=phase, cfg_id=cfg.id(), framework="torch",
        n_params=count_torch(model),
        epochs_ran=ran, stopped_by="early" if ran < cfg.epochs else "max_epoch",
        train_acc=tr_acc, train_loss=tr_loss, val_acc=va_acc, val_loss=va_loss,
        test_acc=test_acc, test_loss=test_loss,
        per_class_recall=str(per_class_recall(yt, yp)),
        lr_history=str([round(float(v), 8) for v in lr_hist]),
        wall_sec=round(wall, 1), **asdict(cfg))


def run(cfg, framework, phase=""):
    """한 조건 한 프레임워크 실행 + 즉시 기록."""
    fn = run_keras if framework == "keras" else run_torch
    row = fn(cfg, phase)
    append_result(row)
    return row


# ============================================================
# 3. 스모크 테스트 — Phase 전에 배선부터 확인
# ============================================================

def smoke_test():
    print("=" * 60)
    print("스모크 테스트 — 1 epoch으로 배선 확인")
    print("=" * 60)
    assert_param_match(BASELINE)
    tiny = replace(BASELINE, epochs=1, seed=0)
    for fw in ("keras", "torch"):
        print(f"\n--- {fw} ---")
        r = run(tiny, fw, phase="smoke")
        print(f"  test_acc {r['test_acc']:.4f} · {r['wall_sec']}초 "
              f"· 파라미터 {r['n_params']:,}")
    print("\n두 줄이 results.csv에 들어갔으면 배선 정상. "
          "이 두 행은 나중에 지워도 된다.")


# ============================================================
# 4. Phase 1 — 학습률 탐색 (12회)
#    "옵티마이저마다 적정 학습률이 다른가?"
# ============================================================

def run_phase1(framework="torch"):
    assert_param_match(BASELINE)
    for opt in ("sgd", "sgd_momentum", "adam"):
        for lr in (1e-4, 3e-4, 1e-3, 1e-2):
            cfg = replace(BASELINE, optimizer=opt, lr=lr,
                          epochs=5, es_patience=99, seed=0)
            print(f"\n===== Phase1 {opt} lr={lr:g} =====")
            run(cfg, framework, phase="p1_lr")


BEST_LR = {          # Phase 1 결과를 보고 채운다
    "sgd": None,
    "sgd_momentum": None,
    "adam": None,
}


# ============================================================
# 5. Phase 2 — 옵티마이저 비교 (9회)
#    "각자 최적 lr에서 비교하면 차이가 남는가?"
# ============================================================

def run_phase2(framework="torch"):
    missing = [k for k, v in BEST_LR.items() if v is None]
    if missing:
        raise RuntimeError(f"BEST_LR을 먼저 채울 것: {missing}")
    for opt, lr in BEST_LR.items():
        for seed in SEEDS:
            cfg = replace(BASELINE, optimizer=opt, lr=lr, seed=seed)
            print(f"\n===== Phase2 {opt} lr={lr:g} seed={seed} =====")
            run(cfg, framework, phase="p2_opt")


# ============================================================
# 6. Phase 3 — 정규화 축 분해 (15회)
#    "정규화 기법들은 대체되는가, 누적되는가?"
#    기준 조건에서 한 축씩만 이동한다.
# ============================================================

AXES = {
    "aug_off":     dict(aug_flip=False, aug_rotate_deg=0.0),
    "dropout_off": dict(dropout=0.0),
    "spatial_on":  dict(spatial_dropout=0.2),
    "bn_off":      dict(use_batchnorm=False),
    "wd_on":       dict(optimizer="adamw", weight_decay=1e-4),
}


def run_phase3(framework="torch"):
    base = replace(BASELINE, lr=BEST_LR.get("adam") or BASELINE.lr)
    for name, change in AXES.items():
        for seed in SEEDS:
            cfg = replace(base, seed=seed, **change)
            assert_param_match(cfg, verbose=False)
            print(f"\n===== Phase3 {name} seed={seed} =====")
            run(cfg, framework, phase=f"p3_{name}")


# ============================================================
# 7. Phase 4 — 프레임워크 (6회)
#    "조건을 완전히 맞추면 프레임워크가 영향을 주는가?"
# ============================================================

def run_phase4():
    base = replace(BASELINE, lr=BEST_LR.get("adam") or BASELINE.lr)
    n = assert_param_match(base)
    print(f"두 모델 파라미터 일치 확인: {n:,}\n")
    for seed in SEEDS:
        for fw in ("keras", "torch"):
            cfg = replace(base, seed=seed)
            print(f"\n===== Phase4 {fw} seed={seed} =====")
            run(cfg, fw, phase="p4_framework")


# ============================================================
# 8. 결과 요약
# ============================================================

def summarize(phase=None):
    """조건별 평균 ± 범위. 단일 숫자를 헤드라인으로 쓰지 않기 위한 것."""
    import csv
    from collections import defaultdict

    rows = list(csv.DictReader(open(RESULTS_CSV, encoding="utf-8")))
    if phase:
        rows = [r for r in rows if r["phase"] == phase]

    g = defaultdict(list)
    for r in rows:
        g[(r["phase"], r["cfg_id"], r["framework"])].append(float(r["test_acc"]))

    print(f"{'조건':<44}{'n':>3}{'평균':>9}{'범위':>16}")
    print("-" * 74)
    for (ph, cid, fw), v in sorted(g.items()):
        rng = f"{min(v)*100:.1f}~{max(v)*100:.1f}" if len(v) > 1 else "—"
        print(f"{ph+' '+cid+' '+fw:<44}{len(v):>3}{np.mean(v)*100:>8.1f}%{rng:>16}")
