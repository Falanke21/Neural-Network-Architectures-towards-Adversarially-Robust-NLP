# Reference: https://github.com/hyunwoongko/transformer
import torch
import torch.nn as nn

from .gated_linear_unit import GatedLinearUnit
from .multi_head_attention import MultiHeadAttention
from .position_wise_feed_forward import PositionwiseFeedForward
from .layer_norm import LayerNorm

USE_GPU = False
device = torch.device(
    'cuda' if USE_GPU and torch.cuda.is_available() else 'cpu')


class EncoderLayer(nn.Module):

    def __init__(self, Config):
        super(EncoderLayer, self).__init__()
        d_model = Config.D_MODEL
        n_head = Config.N_HEAD
        ffn_hidden = Config.FFN_HIDDEN
        drop_prob = Config.DROPOUT
        max_seq_length = Config.MAX_SEQ_LENGTH

        self.attention = MultiHeadAttention(Config=Config)
        self.norm1 = LayerNorm(d_model=d_model)
        self.dropout1 = nn.Dropout(p=drop_prob)

        if hasattr(Config, 'FFN_TYPE') and Config.FFN_TYPE == 'glu':
            self.ffn = GatedLinearUnit(
                d_model=d_model, hidden=ffn_hidden, drop_prob=drop_prob)
        else:
            self.ffn = PositionwiseFeedForward(
                d_model=d_model, hidden=ffn_hidden, drop_prob=drop_prob)
        self.norm2 = LayerNorm(d_model=d_model)
        self.dropout2 = nn.Dropout(p=drop_prob)

    def forward(self, x, src_mask):
        # 1. compute self attention
        _x = x
        x = self.attention(q=x, k=x, v=x, mask=src_mask)

        # 2. add and norm
        x = self.dropout1(x)
        x = self.norm1(x + _x)

        # 3. positionwise feed forward network
        _x = x
        x = self.ffn(x)

        # 4. add and norm
        x = self.dropout2(x)
        x = self.norm2(x + _x)
        return x
