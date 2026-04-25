import torch
import gzip
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.getcwd(), "external/maia-chess/move_prediction"))
from maia_chess_backend.maia.proto.net_pb2 import Net

def parse_layer(layer, shape):
    if layer is None or not layer.HasField('params'):
        return None
    
    expected_size = np.prod(shape)
    buffer = layer.params
    
    # Lc0/Maia uses LINEAR16 encoding: uint16 normalized between min_val and max_val
    if len(buffer) == expected_size * 2:
        params = np.frombuffer(buffer, dtype='<u2').astype(np.float32)
        params /= 65535.0
        min_val = getattr(layer, 'min_val', 0.0)
        max_val = getattr(layer, 'max_val', 1.0)
        data_f32 = params * (max_val - min_val) + min_val
    elif len(buffer) == expected_size * 4:
        # Fallback for float32 if present
        data_f32 = np.frombuffer(buffer, dtype='<f4').astype(np.float32).copy()
    else:
        raise ValueError(f"Weight size mismatch: expected {expected_size}, got {len(buffer)} bytes")
            
    # Safety: Replace any accidental INFs or NaNs
    if np.isinf(data_f32).any() or np.isnan(data_f32).any():
        data_f32 = np.nan_to_num(data_f32, nan=0.0, posinf=1.0, neginf=-1.0)
        
    return torch.from_numpy(data_f32).view(shape)

def load_conv_block(torch_conv, torch_bn, proto_block, in_channels, out_channels, kernel_size):
    if not proto_block: return
    
    w = parse_layer(proto_block.weights, (out_channels, in_channels, kernel_size, kernel_size))
    if w is not None: torch_conv.weight.data.copy_(w)
        
    if proto_block.HasField('biases') and torch_conv.bias is not None:
        b = parse_layer(proto_block.biases, (out_channels,))
        torch_conv.bias.data.copy_(b)

    if torch_bn:
        m = parse_layer(proto_block.bn_means, (out_channels,))
        if m is not None: torch_bn.running_mean.copy_(m)
        v = parse_layer(proto_block.bn_stddivs, (out_channels,))
        if v is not None: torch_bn.running_var.copy_(v**2)
        g = parse_layer(proto_block.bn_gammas, (out_channels,))
        if g is not None: torch_bn.weight.data.copy_(g)
        b = parse_layer(proto_block.bn_betas, (out_channels,))
        if b is not None: torch_bn.bias.data.copy_(b)

def load_se_unit(torch_se, proto_se, channels, reduction=8):
    if not proto_se: return
    reduced = channels // reduction
    
    w1 = parse_layer(proto_se.w1, (reduced, channels))
    if w1 is not None: torch_se.fc[0].weight.data.copy_(w1)
    b1 = parse_layer(proto_se.b1, (reduced,))
    if b1 is not None: torch_se.fc[0].bias.data.copy_(b1)
    
    w2 = parse_layer(proto_se.w2, (channels * 2, reduced))
    if w2 is not None: torch_se.fc[2].weight.data.copy_(w2)
    b2 = parse_layer(proto_se.b2, (channels * 2,))
    if b2 is not None: torch_se.fc[2].bias.data.copy_(b2)

def load_maia_weights(model, pb_gz_path):
    with gzip.open(pb_gz_path, 'rb') as f:
        data = f.read()
    
    net = Net()
    net.ParseFromString(data)
    w = net.weights
    
    load_conv_block(model.input_conv, model.input_bn, w.input, 112, 64, 3)
    
    for i in range(len(w.residual)):
        res_proto = w.residual[i]
        res_torch = model.res_blocks[i]
        load_conv_block(res_torch.conv1, res_torch.bn1, res_proto.conv1, 64, 64, 3)
        load_conv_block(res_torch.conv2, res_torch.bn2, res_proto.conv2, 64, 64, 3)
        load_se_unit(res_torch.se, res_proto.se, 64)
        
    load_conv_block(model.policy_conv1, model.policy_bn1, w.policy1, 64, 64, 3)
    load_conv_block(model.policy_conv2, None, w.policy, 64, 80, 3)
    
    load_conv_block(model.value_conv, model.value_bn, w.value, 64, 32, 1)
    vfw1 = parse_layer(w.ip1_val_w, (128, 32 * 64))
    if vfw1 is not None: model.value_fc1.weight.data.copy_(vfw1)
    vfb1 = parse_layer(w.ip1_val_b, (128,))
    if vfb1 is not None: model.value_fc1.bias.data.copy_(vfb1)
    vfw2 = parse_layer(w.ip2_val_w, (3, 128))
    if vfw2 is not None: model.value_fc2.weight.data.copy_(vfw2)
    vfb2 = parse_layer(w.ip2_val_b, (3,))
    if vfb2 is not None: model.value_fc2.bias.data.copy_(vfb2)

    return model
