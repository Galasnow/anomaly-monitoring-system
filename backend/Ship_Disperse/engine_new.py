import logging
import multiprocessing


import torch
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torchvision.transforms import functional as F
from torch.utils.data import DataLoader
from pycocotools.cocoeval import COCOeval
import os
os.environ['NO_ALBUMENTATIONS_UPDATE'] = '1'
import time

from tqdm import tqdm

from config import NUM_CLASSES, EPOCHS, train_image_dir, train_anno_path, val_anno_path, val_image_dir, BATCH_SIZE, \
    NUMBER_OF_WORKERS, DEVICE, LR, save_dir, early_stop, BATCH_SIZE_TRAIN, BATCH_SIZE_VAL
from dataset_new import CocoDetection
from model import create_model
from utils import create_folder, collate_fn


# 加载数据集
def get_dataset(data_path, annotation_path, transform=True):
    dataset = CocoDetection(
        root=data_path,
        annotation=annotation_path,
        transforms=transform
    )
    return dataset


# 评估函数
def evaluate(model, data_loader, device):
    model.eval()
    results = []

    with torch.no_grad():
        progress_bar = tqdm(data_loader)
        progress_bar.set_description('Evaluating')
        for images, targets in progress_bar:
            images = list(img.to(device) for img in images)
            outputs = model(images)

            for i, output in enumerate(outputs):
                image_id = targets[i]['image_id'].item()
                boxes = output['boxes'].cpu().numpy()
                scores = output['scores'].cpu().numpy()
                labels = output['labels'].cpu().numpy()

                for box, score, label in zip(boxes, scores, labels):
                    result = {
                        "image_id": image_id,
                        "category_id": label,
                        "bbox": [box[0], box[1], box[2] - box[0], box[3] - box[1]],  # xywh
                        "score": float(score)
                    }
                    results.append(result)
                    print(result)
    # 转换为COCO格式
    coco_gt = data_loader.dataset.coco
    coco_dt = coco_gt.loadRes(results)

    # 运行评估
    coco_eval = COCOeval(coco_gt, coco_dt, 'bbox')
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()

    return coco_eval


def train_one_epoch(model, train_loader, val_loader, optimizer, current_epoch):
    model.train()
    start_time = time.time()
    total_loss = 0
    batch_count = 0
    progress_bar = tqdm(train_loader)
    for images, targets in progress_bar:
        images = [image.to(DEVICE) for image in images]

        # 过滤掉负样本（image_id为-1）
        filtered_targets = []
        for target in targets:
            # print(target['image_id'].item())
            if len(target['labels']) > 0:  # 只保留正样本
                filtered_targets.append({k: v.to(DEVICE) for k, v in target.items()})
        if len(filtered_targets) == 0:
            continue

        loss_dict = model(images, filtered_targets)
        losses = sum(loss for loss in loss_dict.values())

        optimizer.zero_grad()
        losses.backward()
        optimizer.step()

        total_loss += losses.item()
        batch_count += 1
        progress_bar.set_description(desc=f'Train Loss: {total_loss / batch_count:.4f}')

    # 验证模型
    coco_eval = evaluate(model, val_loader, DEVICE)
    mAP = coco_eval.stats[0]
    avg_loss = total_loss / batch_count if batch_count > 0 else 0

    logging.info(f"Epoch {current_epoch}/{EPOCHS} - Loss: {avg_loss:.4f} - Time: {time.time() - start_time:.2f}s")
    logging.info(f"Validation mAP: {coco_eval.stats[0]:.4f}")  # AP @ [IoU=0.50:0.95]

    return model, mAP


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # 设置打印级别
    formatter = logging.Formatter('%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s')

    # 设置屏幕打印的格式
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # 创建本次训练保存文件夹
    time_begin = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
    new_save_dir = f'{save_dir}/{time_begin}'
    create_folder(new_save_dir)

    # 设置log保存
    fh = logging.FileHandler(f"{new_save_dir}/test.log", encoding='utf8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logging.info(f'Start time: {time_begin}')

    # 加载数据集
    train_dataset = get_dataset(train_image_dir, train_anno_path, transform=True)
    val_dataset = get_dataset(val_image_dir, val_anno_path, transform=False)

    # 创建数据加载器
    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE_TRAIN, shuffle=True,
        num_workers=NUMBER_OF_WORKERS, collate_fn=collate_fn, drop_last=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE_VAL, shuffle=False,
        num_workers=NUMBER_OF_WORKERS, collate_fn=collate_fn, drop_last=True
    )

    # 创建模型
    model = create_model(NUM_CLASSES)
    model.to(DEVICE)

    # 训练模型
    # model = train_model(model, train_loader, val_loader, new_save_dir, num_epochs=EPOCHS)

    best_mAP = 0.0
    # Extract requisite parameters and instantiate optimizer
    params = [p for p in model.parameters() if p.requires_grad]
    # optim = torch.optim.SGD(params, lr = LR, momentum = MOMENTUM, weight_decay=1e-4)
    optimizer = torch.optim.AdamW(params, lr=LR, weight_decay=1e-3)
    warmup_epoches = 2
    T_max = EPOCHS - warmup_epoches
    eta_min = LR * 1e-3
    lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=optimizer, T_max=T_max, eta_min=eta_min)
    no_update_epoch = 0
    lr_initial = LR * pow(10, -warmup_epoches)

    for current_epoch in range(1, EPOCHS + 1):
        for param_groups in optimizer.param_groups:
            param_groups['lr'] = param_groups['lr'] * 0.99
        if current_epoch <= warmup_epoches:
            for param_groups in optimizer.param_groups:
                param_groups['lr'] = lr_initial * pow(10, current_epoch)
        logging.info(f'lr = {optimizer.state_dict()['param_groups'][0]['lr']}')

        model, mAP = train_one_epoch(model, train_loader, val_loader, optimizer, current_epoch)

        if current_epoch >= warmup_epoches:
            lr_scheduler.step()

        if mAP > best_mAP:
            # 保存模型
            logging.info('Save best model')
            torch.save(model.state_dict(), f"{new_save_dir}/best_model.pth")
            torch.save(model.state_dict(), f"{new_save_dir}/last_model.pth")
            best_mAP = mAP
            no_update_epoch = 0
        else:
            logging.info('Only save last model')
            torch.save(model.state_dict(), f"{new_save_dir}/last_model.pth")
            no_update_epoch += 1
            if no_update_epoch >= early_stop:
                logging.info(f'stop after {early_stop} epoch no improvement')
                break
