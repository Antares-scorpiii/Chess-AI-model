import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import sys
import os

def make_lc0_policy_map():
    sys.path.append(os.path.join(os.getcwd(), "external/maia-chess/move_prediction"))
    # No more silent fallback. If this fails, the model is broken anyway.
    from maia_chess_backend.maia.lc0_az_policy_map import make_map
    return make_map().T

class SEBlock(nn.Module):
    def __init__(self, channels: int, reduction: int = 8):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=True),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels * 2, bias=True)
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c * 2, 1, 1)
        gammas, betas = y.chunk(2, dim=1)
        return torch.sigmoid(gammas) * x + betas

class MaiaResBlock(nn.Module):
    def __init__(self, channels: int, se_ratio: int = 8):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)
        self.se = SEBlock(channels, se_ratio)
    
    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = self.se(out)
        return F.relu(out + residual)

class MaiaNet(nn.Module):
    def __init__(self, channels: int = 64, num_res_blocks: int = 6):
        super().__init__()
        self.input_conv = nn.Conv2d(112, channels, 3, padding=1, bias=False)
        self.input_bn = nn.BatchNorm2d(channels)
        self.res_blocks = nn.ModuleList([MaiaResBlock(channels) for _ in range(num_res_blocks)])
        
        self.policy_conv1 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.policy_bn1 = nn.BatchNorm2d(channels)
        self.policy_conv2 = nn.Conv2d(channels, 80, 3, padding=1, bias=True)
        self.register_buffer('policy_map', torch.from_numpy(make_lc0_policy_map()).float())
        
        self.value_conv = nn.Conv2d(channels, 32, 1, bias=False)
        self.value_bn = nn.BatchNorm2d(32)
        self.value_fc1 = nn.Linear(32 * 8 * 8, 128)
        self.value_fc2 = nn.Linear(128, 3)

    def forward(self, x):
        x = F.relu(self.input_bn(self.input_conv(x)))
        for block in self.res_blocks:
            x = block(x)
            
        p = F.relu(self.policy_bn1(self.policy_conv1(x)))
        p = self.policy_conv2(p).flatten(1)
        p = torch.matmul(p, self.policy_map.T)
        
        v = F.relu(self.value_bn(self.value_conv(x)))
        v = F.relu(self.value_fc1(v.flatten(1)))
        v = self.value_fc2(v)
        
        return p, v
