import torch
from torch.utils.data import DataLoader

from config import NUM_CLASSES, DEVICE, val_image_dir, val_anno_path, BATCH_SIZE, NUMBER_OF_WORKERS, test_image_dir, \
    test_anno_path
from engine_new import get_dataset, evaluate
from model import create_model
from model_archive import create_model_archive
from utils import collate_fn

def evaluate_model(create_model_func, data_loader, path = f'./run/2025-03-20_20-38-05/best_model.pth'):
    model = create_model_func(NUM_CLASSES)
    model.load_state_dict(
        torch.load(path, map_location=DEVICE,
                   weights_only=True))  # final#红海108-all  178-2个 140-1个
    model.eval()  # 确保模型处于评估模式
    model.to(DEVICE)
    coco_eval = evaluate(model, data_loader, DEVICE)
    mAP = coco_eval.stats[0]
    return mAP

if __name__ == "__main__":

    test_dataset = get_dataset(test_image_dir, test_anno_path, train=False)

    test_loader = DataLoader(
        test_dataset, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUMBER_OF_WORKERS, collate_fn=collate_fn, drop_last=True
    )

    mAP_1 = evaluate_model(create_model_archive, test_loader, path = f'./run/2025-03-06_20-13-27/best_model.pth')
    print(mAP_1)
    mAP_2 = evaluate_model(create_model_archive, test_loader, path = f'./run/2025-03-20_20-38-05/best_model.pth')
    print(mAP_2)
    mAP_3 = evaluate_model(create_model_archive, test_loader, path = f'./run/2025-03-27_16-08-11/best_model.pth')
    print(mAP_3)

    model_2 = create_model_archive(NUM_CLASSES)