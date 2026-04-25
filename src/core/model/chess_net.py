import torch
import torch.nn as nn
import torch.nn.functional as F

class ResBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)
    
    def forward(self, x):
        residual = x
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        return F.relu(x + residual)

class ChessNet(nn.Module):
    """
    Behavioral cloning network for chess move prediction.
    Input:  (batch, 19, 8, 8) board tensor (including time plane)
    Output: (batch, 4096) move logits
    """
    def __init__(self, channels: int = 64, num_res_blocks: int = 4, use_value_head: bool = False, dropout: float = 0.3):
        super().__init__()
        self.use_value_head = use_value_head
        
        self.input_conv = nn.Sequential(
            nn.Conv2d(19, channels, 3, padding=1, bias=False),  # 19 channels for time-awareness
            nn.BatchNorm2d(channels),
            nn.ReLU()
        )
        
        self.res_blocks = nn.Sequential(*[ResBlock(channels) for _ in range(num_res_blocks)])
        
        self.policy_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(channels * 8 * 8, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 4096)
        )
        
        if use_value_head:
            self.value_head = nn.Sequential(
                nn.Flatten(),
                nn.Linear(channels * 8 * 8, 256),
                nn.ReLU(),
                nn.Linear(256, 1),
                nn.Tanh()
            )
    
    def forward(self, x):
        x = self.input_conv(x)
        x = self.res_blocks(x)
        
        policy = self.policy_head(x)
        
        if self.use_value_head:
            value = self.value_head(x)
            return policy, value
        
        return policy
