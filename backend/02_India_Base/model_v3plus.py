import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.model_zoo as model_zoo
import torchvision.models as models
import numpy as np
import math


# model_url = 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth'
class _PositionAttentionModule(nn.Module):
    """ Position attention module"""

    def __init__(self, in_channels, **kwargs):
        super(_PositionAttentionModule, self).__init__()
        self.conv_b = nn.Conv2d(in_channels, in_channels // 8, 1)
        self.conv_c = nn.Conv2d(in_channels, in_channels // 8, 1)
        self.conv_d = nn.Conv2d(in_channels, in_channels, 1)
        self.alpha = nn.Parameter(torch.zeros(1))
        # 类型转换函数，将一个不可训练的类型Tensor转换成可以训练的类型parameter并将这个parameter绑定到这个module里面
        # (net.parameter()中就有这个绑定的parameter
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        batch_size, _, height, width = x.size()
        # print(batch_size)
        feat_b = self.conv_b(x).view(batch_size, -1, height * width).permute(0, 2, 1)
        # print("feat_b", feat_b.shape)
        feat_c = self.conv_c(x).view(batch_size, -1, height * width)
        # print("feat_c", feat_c.shape)
        attention_s = self.softmax(torch.bmm(feat_b, feat_c))
        # print("attention_s", attention_s.shape)
        feat_d = self.conv_d(x).view(batch_size, -1, height * width)
        # print("feat_d", feat_d.shape)
        feat_e = torch.bmm(feat_d, attention_s.permute(0, 2, 1)).view(batch_size, -1, height, width)
        # print("feat_e", feat_e.shape)
        # e = torch.bmm(feat_d, attention_s.permute(0, 2, 1))
        # print("e", e.shape)
        # e1 = attention_s.permute(0, 2, 1)
        # print("e1:", e1.shape)
        out = self.alpha * feat_e + x
        # print("out", out.shape)
        # print("x", x.shape)
        return out


class _ChannelAttentionModule(nn.Module):
    """Channel attention module"""

    def __init__(self, **kwargs):
        super(_ChannelAttentionModule, self).__init__()
        self.beta = nn.Parameter(torch.zeros(1))
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        batch_size, _, height, width = x.size()
        feat_a = x.view(batch_size, -1, height * width)
        feat_a_transpose = x.view(batch_size, -1, height * width).permute(0, 2, 1)
        attention = torch.bmm(feat_a, feat_a_transpose)
        # print("attention", attention.shape)
        # 指定维度取出最大值
        attention_new = torch.max(attention, dim=-1, keepdim=True)[0].expand_as(attention) - attention
        # print("attention_new", attention_new.shape)
        attention = self.softmax(attention_new)

        feat_e = torch.bmm(attention, feat_a).view(batch_size, -1, height, width)
        out = self.beta * feat_e + x
        # print("self.beta", self.beta)
        # print("x", x.shape)
        # print("out", out.shape)
        return out


class Atrous_Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, rate=1, downsample=None):
        super(Atrous_Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride,
                               dilation=rate, padding=rate, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


class Atrous_ResNet_features(nn.Module):

    def __init__(self, n_channels, block, layers, pretrained=False):
        super(Atrous_ResNet_features, self).__init__()
        self.inplanes = 64

        self.conv1 = nn.Conv2d(n_channels, 64, kernel_size=7, stride=2, padding=3,
                               bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0], stride=1, rate=1)
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2, rate=1)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2, rate=1)
        self.layer4 = self._make_MG_unit(block, 512, stride=1, rate=2)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

        if pretrained:
            print('load the pre-trained model.')
            resnet = models.resnet152(pretrained)
            self.conv1 = resnet.conv1
            self.bn1 = resnet.bn1
            self.layer1 = resnet.layer1
            self.layer2 = resnet.layer2

    def _make_layer(self, block, planes, blocks, stride=1, rate=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, rate, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def _make_MG_unit(self, block, planes, blocks=[1, 2, 4], stride=1, rate=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, rate=blocks[0] * rate, downsample=downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, len(blocks)):
            layers.append(block(self.inplanes, planes, stride=1, rate=blocks[i] * rate))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        conv2 = x
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        return x, conv2


class Atrous_module(nn.Module):
    def __init__(self, inplanes, planes, rate):
        super(Atrous_module, self).__init__()
        self.atrous_convolution = nn.Conv2d(inplanes, planes, kernel_size=3,
                                            stride=1, padding=rate, dilation=rate)
        self.batch_norm = nn.BatchNorm2d(planes)

    def forward(self, x):
        x = self.atrous_convolution(x)
        x = self.batch_norm(x)

        return x


class DeepLabv3_plus(nn.Module):
    def __init__(self, n_channels=4, n_classes=1, **kwargs):
        super(DeepLabv3_plus, self).__init__()
        block = Atrous_Bottleneck
        self.resnet_features = Atrous_ResNet_features(n_channels, block, [3, 8, 36], False)

        rates = [1, 6, 12, 18]
        self.aspp1 = Atrous_module(2048, 256, rate=rates[0])
        self.aspp2 = Atrous_module(2048, 256, rate=rates[1])
        self.aspp3 = Atrous_module(2048, 256, rate=rates[2])
        self.aspp4 = Atrous_module(2048, 256, rate=rates[3])
        self.image_pool = nn.Sequential(nn.AdaptiveMaxPool2d(1),
                                        nn.Conv2d(2048, 256, kernel_size=1))

        self.fc1 = nn.Sequential(nn.Conv2d(1280, 256, kernel_size=1),
                                 nn.BatchNorm2d(256))

        self.pam = _PositionAttentionModule(256, **kwargs)
        self.cam = _ChannelAttentionModule(**kwargs)


        self.reduce_conv2 = nn.Sequential(nn.Conv2d(256, 48, kernel_size=1),
                                          nn.BatchNorm2d(48))
        self.last_conv = nn.Sequential(nn.Conv2d(304, 256, kernel_size=3, stride=1, padding=1),
                                       nn.BatchNorm2d(256),
                                       nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
                                       nn.BatchNorm2d(256),
                                       nn.Conv2d(256, n_classes, kernel_size=1, stride=1))
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):

        x, conv2 = self.resnet_features(x)
        x1 = self.aspp1(x)
        x2 = self.aspp2(x)
        x3 = self.aspp3(x)
        x4 = self.aspp4(x)
        x5 = self.image_pool(x)
        x5 = F.interpolate(x5, size=x4.size()[2:], mode='nearest')

        x = torch.cat((x1, x2, x3, x4, x5), dim=1)
        x = self.fc1(x)

        feat_p = self.pam(x)
        feat_c = self.cam(x)
        feat_fusion = feat_p + feat_c

        x = F.interpolate(feat_fusion, scale_factor=(4, 4), mode='bilinear')

        low_lebel_features = self.reduce_conv2(conv2)

        x = torch.cat((x, low_lebel_features), dim=1)
        x = self.last_conv(x)
        x = F.interpolate(x, scale_factor=(4, 4), mode='bilinear')
        x = self.sigmoid(x)
        return x


if __name__ == '__main__':
    # deeplabv3plus = DeepLabv3_plus(n_channels=4, n_classes=1)
    deeplabv3plus = Atrous_ResNet_features(4, Atrous_Bottleneck, [3, 8, 36], False)
    # 16是batch_size，即每批次喂网络16个；3是3个通道，如果RGB图片，则为3,如果灰度图像，则为1；256*256是输入的大小
    # images = Variable(torch.rand(16, 3, 256, 256).cuda())
    # prediction = unet(images).cuda()
    images = torch.rand(1, 4, 256, 256)
    prediction = deeplabv3plus(images)
    print("prediction type:", type(prediction))
    print(prediction.size())
