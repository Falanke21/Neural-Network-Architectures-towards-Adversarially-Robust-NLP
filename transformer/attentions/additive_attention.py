# Dzmitry Bahdanau, Kyunghyun Cho, and Yoshua Bengio. Neural machine
# translation by jointly learning to align and translate, 2016. pages 2
# https://arxiv.org/abs/1409.0473
# Slightly modified to work with self-attention.

import torch
import torch.nn as nn


class AdditiveAttention(nn.Module):
    """
    compute additive self-attention

    Query : given sentence that we focused on (decoder)
    Key : every sentence to check relationship with Query(encoder)
    Value : every sentence same with Key (encoder)
    """

    def __init__(self, d_tensor):
        super(AdditiveAttention, self).__init__()
        self.va = nn.Linear(d_tensor, 1)
        self.softmax = nn.Softmax(dim=-1)
        print("Using Additive Attention")

    def forward(self, q, k, v, mask=None):
        # input is 4 dimension tensor
        batch_size, head, length, d_tensor = k.size()

        # 1. calculate alignment model output tensor e
        # [batch_size, head, length, d_tensor]
        e3 = (q + k) / 2  # [batch_size, head, length, d_tensor]
        e = torch.tanh(e3)
        e = self.va(e).squeeze(-1)  # [batch_size, head, length]

        # 2. apply masking (opt)
        if mask is not None:
            e = e.masked_fill(mask == 0, -10000)

        # 3. pass them softmax to make [0, 1] range
        alpha = self.softmax(e)  # [batch_size, head, length]

        # 4. multiply with Value
        result = alpha.unsqueeze(-1) * v  # [batch_size, head, length, d_tensor]

        return result
