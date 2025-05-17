import torchvision
from torch import nn
from torchvision.models import ResNet50_Weights, resnet50
from torchvision.models.detection.anchor_utils import AnchorGenerator
from torchvision.models.detection.backbone_utils import _resnet_fpn_extractor, _validate_trainable_layers
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor, FasterRCNN, FasterRCNN_ResNet50_FPN_V2_Weights, \
    FastRCNNConvFCHead
from torchvision.models.detection.rpn import RPNHead


def create_model_archive(num_classes):
    #Load the pre-trained model
    # model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained = True)
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn_v2(weights='COCO_V1')
    #Get the number of input features to the original box predictor
    in_features = model.roi_heads.box_predictor.cls_score.in_features

    #Define a new box predictor with the requisite number of classes
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    return model
