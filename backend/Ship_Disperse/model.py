import torchvision
from torch import nn
from torchvision.models import ResNet50_Weights, resnet50
from torchvision.models.detection.anchor_utils import AnchorGenerator
from torchvision.models.detection.backbone_utils import _resnet_fpn_extractor, _validate_trainable_layers
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor, FasterRCNN, FasterRCNN_ResNet50_FPN_V2_Weights, \
    FastRCNNConvFCHead
from torchvision.models.detection.rpn import RPNHead


def create_model(num_classes):
    #Load the pre-trained model
    # model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained = True)
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn_v2(weights='COCO_V1')
    #Get the number of input features to the original box predictor
    in_features = model.roi_heads.box_predictor.cls_score.in_features

    #Define a new box predictor with the requisite number of classes
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    return model


def create_model_new(num_classes, progress=True):
    # from "torchvision\models\detection\faster_rcnn.py - fasterrcnn_resnet50_fpn_v2"
    weights = ("pretrained", FasterRCNN_ResNet50_FPN_V2_Weights.COCO_V1)
    weights_backbone = ("pretrained_backbone", ResNet50_Weights.IMAGENET1K_V1)
    weights = FasterRCNN_ResNet50_FPN_V2_Weights.verify(weights)
    weights_backbone = ResNet50_Weights.verify(weights_backbone)

    is_trained = weights is not None or weights_backbone is not None
    trainable_backbone_layers = _validate_trainable_layers(is_trained, None, 5, 3)

    backbone = resnet50(weights=weights_backbone, progress=progress)
    backbone = _resnet_fpn_extractor(backbone, trainable_backbone_layers, norm_layer=nn.BatchNorm2d)
    rpn_anchor_generator = AnchorGenerator(
        sizes=((4, 8, 16, 24, 32),),
        aspect_ratios=((0.25, 0.5, 1.0, 2.0, 4.0),)
    )
    rpn_head = RPNHead(backbone.out_channels, rpn_anchor_generator.num_anchors_per_location()[0], conv_depth=2)
    box_head = FastRCNNConvFCHead(
        (backbone.out_channels, 7, 7), [256, 256, 256, 256], [1024], norm_layer=nn.BatchNorm2d
    )
    model = FasterRCNN(
        backbone,
        num_classes=num_classes,
        rpn_anchor_generator=rpn_anchor_generator,
        rpn_head=rpn_head,
        box_head=box_head,
    )

    if weights is not None:
        model.load_state_dict(weights.get_state_dict(progress=progress, check_hash=True))

    # Get the number of input features to the original box predictor
    in_features = model.roi_heads.box_predictor.cls_score.in_features

    # Define a new box predictor with the requisite number of classes
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    return model
