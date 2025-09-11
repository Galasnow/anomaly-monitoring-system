import copy

from pycocotools.cocoeval import COCOeval
from torch.utils.data import DataLoader
import multiprocessing
import torch.distributed as dist

from tqdm import tqdm

from config import (DEVICE, NUM_CLASSES, EPOCHS, save_dir, SAVE_PLOTS_EPOCH, LR, RESIZE_TO, CLASSES,
                    NUMBER_OF_WORKERS, BATCH_SIZE, train_label_dir, train_image_dir, train_anno_path,
                    val_image_dir, val_label_dir, val_anno_path, early_stop)
from dataset import PlatformDataset
from evaluator import CocoDetectionEvaluator
from utils import Averager, create_folder, collate_fn
# from dataset import AirplaneDataset
from model import create_model

import torch
import matplotlib.pyplot as plt
import time
import logging
import numpy as np

plt.style.use('ggplot')


def train(train_data_loader, model, optim, train_loss_list, train_loss_hist):
    # logging.info('Training')
    model.train()
    # Keep track of total iterations
    global train_iter

    # Instatiate tqdm progress bar
    prog_bar = tqdm(train_data_loader, total=len(train_data_loader))

    # Iterate over each batch
    for images, targets in prog_bar:
        # Clear the gradient before forward pass
        optim.zero_grad()
        # images = torch.as_tensor(images, device=DEVICE)
        # targets = torch.as_tensor(targets, device=DEVICE)

        # Push data to device
        images = [image.to(DEVICE) for image in images]
        targets = [{k: v.to(DEVICE) for k, v in t.items()} for t in targets]

        # Forward pass
        loss_dict = model(images, targets)

        # logging.info(f'loss_dict = {loss_dict}')

        # Calculate the total loss in this batch
        losses = sum(loss for loss in loss_dict.values())
        loss_train = losses.item()

        # Append batch loss to the list of losses for plotting and send to averager to calculate epoch loss
        train_loss_list.append(loss_train)
        train_loss_hist.send(loss_train)

        # Perform backward step and update weights
        losses.backward()
        optim.step()

        # Update training iterations
        train_iter += 1

        # Update the progrss bar
        prog_bar.set_description(desc=f'Train Loss: {train_loss_hist.value():.4f}')


# def valid(valid_data_loader, model, valid_loss_list, valid_loss_hist):
#     # logging.info('Validating')
#     model.eval()
#     # Keep track of total iterations
#     global valid_iter
#
#     # Instatiate tqdm progress bar
#     prog_bar = tqdm(valid_data_loader, total=len(valid_data_loader))
#
#     for images, targets in prog_bar:
#         # Push data to device
#
#         images = [image.to(DEVICE) for image in images]
#         targets = [{k: v.to(DEVICE) for k, v in t.items()} for t in targets]
#
#         # Foward pass, no gradient
#         with torch.no_grad():
#             loss_dict = model(images, targets)
#         print(loss_dict)
#         # Calculate total loss in batch
#         # losses = sum(loss for loss in loss_dict.values())
#         # loss_val = losses.item()
#
#         # Append batch loss to list of losses and send to averager
#         # valid_loss_list.append(loss_val)
#         # valid_loss_hist.send(loss_val)
#
#         # Update valid iterations
#         valid_iter += 1
#
#         # Update the progress bar
#         # prog_bar.set_description(desc=f'Val Loss: {valid_loss_hist.value():.4f}')


def evaluate(model, data_loader, device):
    model.eval()
    results = []

    with torch.no_grad():
        for images, targets in data_loader:
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

    # 转换为COCO格式
    coco_gt = data_loader.dataset.coco_api
    coco_dt = coco_gt.loadRes(results)

    # 运行评估
    coco_eval = COCOeval(coco_gt, coco_dt, 'bbox')
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()

    return coco_eval


def build_evaluator(cfg, dataset):
    return CocoDetectionEvaluator(dataset)

#
# def evaluate():
#     results = {}
#     for res in validation_step_outputs:
#         results.update(res)
#     all_results = (
#         gather_results(results)
#         if dist.is_available() and dist.is_initialized()
#         else results
#     )
#     if all_results:
#         eval_results = CocoDetectionEvaluator.evaluate(
#             all_results, new_save_dir
#         )

if __name__ == '__main__':
    time_begin = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
    new_save_dir = f'{save_dir}/{time_begin}'
    create_folder(new_save_dir)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # 设置打印级别
    formatter = logging.Formatter('%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s')

    # 设置屏幕打印的格式
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # 设置log保存
    fh = logging.FileHandler(f"{new_save_dir}/test.log", encoding='utf8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logging.info(f'Start time: {time_begin}')

    # Instantiate Dataset instances
    # train_dataset = AirplaneDataset(TRAIN_DIR, RESIZE_TO, RESIZE_TO, CLASSES, get_train_transform())
    # valid_dataset = AirplaneDataset(VALID_DIR, RESIZE_TO, RESIZE_TO, CLASSES, get_valid_transform())
    # train_dataset = AirplaneDataset(TRAIN_DIR, RESIZE_TO, RESIZE_TO, CLASSES, DEVICE, train_annotations_file_path, None)
    # valid_dataset = AirplaneDataset(VALID_DIR, RESIZE_TO, RESIZE_TO, CLASSES, DEVICE, valid_annotations_file_path, None)
    multiprocessing.set_start_method('spawn')
    train_dataset = PlatformDataset(train_image_dir, train_label_dir, train_anno_path, RESIZE_TO, RESIZE_TO, CLASSES, DEVICE, None,
                                    aug=True)
    valid_dataset = PlatformDataset(val_image_dir, val_label_dir, val_anno_path, RESIZE_TO, RESIZE_TO, CLASSES, DEVICE, None,
                                    aug=False)
    # Instantiate DataLoader instances
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=NUMBER_OF_WORKERS, collate_fn=collate_fn, drop_last=True)

    valid_loader = DataLoader(valid_dataset, batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=NUMBER_OF_WORKERS, collate_fn=collate_fn, drop_last=True)

    # Give some console output on the dataset lengths
    logging.info(f'Number of training images: {len(train_dataset)}')
    logging.info(f'Number of validation images: {len(valid_dataset)}')

    # Instantiate model and push to device
    model = create_model(num_classes=NUM_CLASSES)
    model.to(DEVICE)

    logging.info(f'Use device: {DEVICE}')

    # Extract requisite parameters and instantiate optimizer
    params = [p for p in model.parameters() if p.requires_grad]
    # optim = torch.optim.SGD(params, lr = LR, momentum = MOMENTUM, weight_decay=1e-4)
    optim = torch.optim.AdamW(params, lr=LR, weight_decay=1e-3)
    warmup_epoches = 3
    T_max = EPOCHS - warmup_epoches
    eta_min = LR * 1e-3
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=optim, T_max=T_max, eta_min=eta_min)
    # Initialize helper objects, lists, and counters
    train_loss_hist = Averager()
    valid_loss_hist = Averager()
    train_iter = 1
    valid_iter = 1
    train_loss_list = []
    valid_loss_list = []

    # Define the model name
    MODEL_NAME = 'model'
    min_loss = 1e5

    lr_initial = LR * pow(10, -warmup_epoches)
    # Train for a given number of epochs:
    no_update_epoch = 0
    for e in range(1, EPOCHS + 1):
        # logging.info(f'\nEPOCH {e} / {EPOCHS}\n')
        logging.info(f'Epoch {e} / {EPOCHS}')
        for param_groups in optim.param_groups:
            param_groups['lr'] = param_groups['lr'] * 0.99
        if e <= warmup_epoches:
            for param_groups in optim.param_groups:
                param_groups['lr'] = lr_initial * pow(10, e)
        logging.info(f'lr = {optim.state_dict()['param_groups'][0]['lr']}')

        # Reset the training and validation averagers
        train_loss_hist.reset()
        valid_loss_hist.reset()

        # Create two subplots, one for training and one for validation
        f1, train_ax = plt.subplots()
        f2, valid_ax = plt.subplots()

        epoch_start_time = time.time()

        # Training
        train(train_loader, model, optim, train_loss_list, train_loss_hist)

        # Validation
        # valid(valid_loader, model, valid_loss_list, valid_loss_hist)
        evaluate(model, valid_loader, DEVICE)
        coco_eval =  evaluate(model, valid_loader, DEVICE)
        print(f"Validation mAP: {coco_eval.stats[0]:.4f}")  # AP @ [IoU=0.50:0.95]

        # Display the training and validation loss for this epochs
        logging.info(f'Epoch training loss: {train_loss_hist.value():.3f}')
        logging.info(f'Epoch validation loss: {valid_loss_hist.value():.3f}')

        # Complete timing
        # logging.info(f'Epoch time: {time.time() - stime}')
        logging.info(f'Epoch time: {time.time() - epoch_start_time}')

        torch.save(model.state_dict(), f'{new_save_dir}/last_model.pth')
        # logging.info('SAVING LAST MODEL COMPLETE')
        logging.info('Save last model')
        # If required, save model
        # if e % SAVE_MODEL_EPOCH == 0:
        if valid_loss_hist.value() < min_loss:
            min_loss = valid_loss_hist.value()
            torch.save(model.state_dict(), f'{new_save_dir}/best_model.pth')
            logging.info(f'Save best model at epoch {e}')
            # logging.info('SAVING BEST MODEL COMPLETE')
            no_update_epoch = 0
        else:
            no_update_epoch += 1
            if no_update_epoch >= early_stop:
                logging.info(f'stop after {early_stop} epoch no improvement')
                break
        # If required, save plot
        if e % SAVE_PLOTS_EPOCH == 0:
            train_ax.plot(train_loss_list, color='blue')
            train_ax.set_xlabel('iterations')
            train_ax.set_ylabel('train loss')
            f1.savefig(f'{new_save_dir}/train_loss.png')
            valid_ax.plot(valid_loss_list, color='red')
            valid_ax.set_xlabel('iterations')
            train_ax.set_ylabel('validation loss')
            f2.savefig(f'{new_save_dir}/valid_loss.png')
            logging.info('save plot')
            # logging.info('SAVING PLOTS COMPLETE')

        # Save at least once at the end
        if e == EPOCHS:
            # Save plots
            train_ax.plot(train_loss_list, color='blue')
            train_ax.set_xlabel('iterations')
            train_ax.set_ylabel('train loss')
            f1.savefig(f'{new_save_dir}/train_loss_final.png')
            valid_ax.plot(valid_loss_list, color='red')
            valid_ax.set_xlabel('iterations')
            train_ax.set_ylabel('validation loss')
            f2.savefig(f'{new_save_dir}/valid_loss_final.png')

        # Close all plots
        plt.close('all')

        if e >= warmup_epoches:
            scheduler.step()
