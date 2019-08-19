import torch
import torch.nn.functional as F
from torch import nn
from torchvision import models

from utils.training import initialize_weights
from .config_model import vgg19_bn_path, res152_path, dense201_path


class _FCN8Base(nn.Module):
    def __init__(self):
        super(_FCN8Base, self).__init__()
        self.features3 = None
        self.features4 = None
        self.features5 = None
        self.fconv3 = None
        self.fconv4 = None
        self.fconv5 = None

    def forward(self, x):
        # features
        f_y3 = self.features3(x)
        f_y4 = self.features4(f_y3)
        f_y5 = self.features5(f_y4)
        # labels
        y5 = self.fconv5(f_y5)
        y4 = self.fconv4(f_y4)
        y3 = self.fconv3(f_y3)

        y = y4 + F.upsample(y5, y4.size()[2:], None, 'bilinear')
        y = y3 + F.upsample(y, y3.size()[2:], None, 'bilinear')
        y = F.upsample(y, x.size()[2:], None, 'bilinear')
        return y, f_y5


class FCN8VGG(_FCN8Base):
    def __init__(self, num_classes, pretrained=True):
        super(FCN8VGG, self).__init__()
        vgg = models.vgg19_bn()
        if pretrained:
            vgg.load_state_dict(torch.load(vgg19_bn_path))
        features = list(vgg.features.children())
        self.features3 = nn.Sequential(*features[0:27])
        self.features4 = nn.Sequential(*features[27:40])
        self.features5 = nn.Sequential(*features[40:])
        self.fconv3 = nn.Conv2d(256, num_classes, kernel_size=1)
        self.fconv4 = nn.Conv2d(512, num_classes, kernel_size=1)
        self.fconv5 = nn.Sequential(
            nn.Conv2d(512, 4096, kernel_size=7),
            nn.ReLU(inplace=True),
            nn.Dropout(),
            nn.Conv2d(4096, 4096, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Dropout(),
            nn.Conv2d(4096, num_classes, kernel_size=1)
        )
        initialize_weights(self.fconv3, self.fconv4, self.fconv5)


class FCN8ResNet(_FCN8Base):
    def __init__(self, num_classes, pretrained=True):
        super(FCN8ResNet, self).__init__()
        res = models.resnet152()
        if pretrained:
            res.load_state_dict(torch.load(res152_path))
        self.features3 = nn.Sequential(
            res.conv1, res.bn1, res.relu, res.maxpool, res.layer1, res.layer2
        )
        self.features4 = res.layer3
        self.features5 = res.layer4
        self.fconv3 = nn.Conv2d(512, num_classes, kernel_size=1)
        self.fconv4 = nn.Conv2d(1024, num_classes, kernel_size=1)
        self.fconv5 = nn.Conv2d(2048, num_classes, kernel_size=7)
        initialize_weights(self.fconv3, self.fconv4, self.fconv5)


class FCN8DenseNet(_FCN8Base):
    def __init__(self, num_classes, pretrained=True):
        super(FCN8DenseNet, self).__init__()
        dense = models.densenet201()
        if pretrained:
            dense.load_state_dict(torch.load(dense201_path))
        features = list(dense.features.children())
        self.features3 = nn.Sequential(*features[:8])
        self.features4 = nn.Sequential(*features[8:10])
        self.features5 = nn.Sequential(*features[10:])
        self.fconv3 = nn.Sequential(
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, num_classes, kernel_size=1)
        )
        self.fconv4 = nn.Sequential(
            nn.BatchNorm2d(896),
            nn.ReLU(inplace=True),
            nn.Conv2d(896, num_classes, kernel_size=1)
        )
        self.fconv5 = nn.Sequential(
            nn.ReLU(inplace=True),
            nn.Conv2d(1920, num_classes, kernel_size=7)
        )
        initialize_weights(self.fconv3, self.fconv4, self.fconv5)
