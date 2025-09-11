import torch
import torchvision
from torch import nn
from torchvision.models import ResNet50_Weights, resnet50
from torchvision.models.detection.anchor_utils import AnchorGenerator
from torchvision.models.detection.backbone_utils import _resnet_fpn_extractor, _validate_trainable_layers, \
    resnet_fpn_backbone
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor, FasterRCNN, FasterRCNN_ResNet50_FPN_V2_Weights, \
    FastRCNNConvFCHead
from torchvision.models.detection.rpn import RPNHead

from config import NUM_CLASSES


def create_model(num_classes):
    # Load the pre-trained model
    # model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained = True)

    anchor_ratios = (0.25, 0.5, 1.0, 2.0, 4.0)
    anchor_sizes = ((2,), (4,), (8,), (16,), (24,))  # 不同特征层的anchor大小
    aspect_ratios = (tuple(anchor_ratios),) * len(anchor_sizes)  # 为每一层应用相同的长宽比例
    # 创建自定义的anchor生成器
    anchor_generator = AnchorGenerator(
        sizes=anchor_sizes,
        aspect_ratios=aspect_ratios
    )

    model = torchvision.models.detection.fasterrcnn_resnet50_fpn_v2(weights='COCO_V1')
    # Get the number of input features to the original box predictor
    in_features = model.roi_heads.box_predictor.cls_score.in_features

    # Define a new box predictor with the requisite number of classes
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    # anchor_ratios = (0.25, 0.5, 1.0, 2.0, 4.0)
    # # 获取原始anchor生成器的sizes
    # original_anchor_generator = model.rpn.anchor_generator
    # anchor_sizes = original_anchor_generator.sizes
    # print(f'{anchor_sizes = }')
    # # anchor_sizes = ((2,), (4,), (8,), (16,), (24,))  # 不同特征层的anchor大小
    # aspect_ratios = (tuple(anchor_ratios),) * len(anchor_sizes)  # 为每一层应用相同的长宽比例
    # # 创建自定义的anchor生成器
    # anchor_generator = AnchorGenerator(
    #     sizes=anchor_sizes,
    #     aspect_ratios=aspect_ratios
    # )
    # model.rpn.anchor_generator = anchor_generator

    return model


def create_custom_faster_rcnn(num_classes, anchor_ratios=None, pretrained=True):
    """
       创建自定义anchor长宽比的Faster R-CNN模型

       参数:
           num_classes (int): 包括背景的分类数量
           anchor_ratios (list[float]): anchor的长宽比例列表，默认为[0.5, 1.0, 2.0]
           pretrained (bool): 是否使用预训练权重
       """
    # 默认的anchor长宽比例
    if anchor_ratios is None:
        anchor_ratios = (0.25, 0.5, 1.0, 2.0, 4.0)

    # 使用torchvision中较新的fasterrcnn_resnet50_fpn_v2作为基础模型
    # 首先加载预训练的主干网络
    backbone = resnet_fpn_backbone('resnet50', pretrained=pretrained, trainable_layers=5)

    # 定义anchor生成器的参数
    # 这里我们保持默认的anchor大小，只修改长宽比例
    anchor_sizes = ((2,), (4,), (8,), (16,), (24,))  # 不同特征层的anchor大小
    aspect_ratios = (tuple(anchor_ratios),) * len(anchor_sizes)  # 为每一层应用相同的长宽比例

    # 创建自定义的anchor生成器
    anchor_generator = AnchorGenerator(
        sizes=anchor_sizes,
        aspect_ratios=aspect_ratios
    )

    # ROI pooling层参数
    roi_pooler = torchvision.ops.MultiScaleRoIAlign(
        featmap_names=['0', '1', '2', '3'],
        output_size=7,
        sampling_ratio=2
    )

    # 创建Faster R-CNN模型
    model = FasterRCNN(
        backbone,
        num_classes=num_classes,
        rpn_anchor_generator=anchor_generator,
        box_roi_pool=roi_pooler,
        image_mean=(0.4, 0.4),
        image_std=(0.2, 0.2)
    )

    return model

if __name__ == "__main__":
    model = create_custom_faster_rcnn(NUM_CLASSES)
    model.eval()
    x = torch.rand(1, 2, 480, 480)
    predictions = model(x)
    print(predictions)
