# COSFORMER : RETHINKING SOFTMAX IN ATTENTION
# (https://arxiv.org/abs/2202.08791)
# https://github.com/OpenNLPLab/cosFormer/blob/main/cosformer.py
import torch
import torch.nn as nn
import numpy as np


class RobustAttention(nn.Module):
	"""
	compute RobustAttention

	Query : given sentence that we focused on (decoder)
	Key : every sentence to check relationship with Query(encoder)
	Value : every sentence same with Key (encoder)
	"""

	def __init__(self, block_size=15):
		super(RobustAttention, self).__init__()
		self.block_size = block_size
		print(f"Using Robust Attention")

	# adopting code from https://github.com/OpenNLPLab/cosFormer/blob/main/cosformer.py
	def get_index(self, seq_len):
		index = np.pi / 2 * torch.arange(1, seq_len + 1).reshape(1, -1, 1)

		return nn.Parameter(index, requires_grad=False)
	
	def cos_reweight(self, q, k, v):
		batch_size, head, length, d_tensor = k.size()
		# adopting code from https://github.com/OpenNLPLab/cosFormer/blob/main/cosformer.py
		# L = target length, S = source length, N = batch_size,
		# h = head, E = d_model, d = d_tensor
		bsz = batch_size
		num_heads = head
		head_dim = d_tensor
		tgt_len = length
		src_len = length
		eps = 1e-6
		# multihead reshape
		# (N, h, L, d) -> (N * h, L, d)
		q = q.contiguous().view(batch_size * head, length, d_tensor)
		k = k.contiguous().view(batch_size * head, length, d_tensor)
		v = v.contiguous().view(batch_size * head, length, d_tensor)

		m = length
		# get index and send to cuda
		weight_index = self.get_index(m).to(q)
		# (N * h, L, 2 * d)
		q_ = torch.cat([q * torch.sin(weight_index[:, :tgt_len, :] / m),
					   q * torch.cos(weight_index[:, :tgt_len, :] / m)], dim=-1)
		# (N * h, S, 2 * d)
		k_ = torch.cat([k * torch.sin(weight_index[:, :src_len, :] / m),
					   k * torch.cos(weight_index[:, :src_len, :] / m)], dim=-1)

		# Need to improve speed!
		# (N * h, L, 2 * d) (N * h, L, d) -> (N * h, L, h, 2 * d, d)
		kv_ = torch.einsum("nld,nlm->nldm", k_, v)
		# (N * h, L, 2 * d, d) -> (N * h, L, 2 * d, d)
		kv_cum = torch.cumsum(kv_, dim=1)
		# (N * h, L, 2 * d) (N * h, L, 2 * d, d) -> (N * h, L, d)
		qkv = torch.einsum("nld,nldm->nlm", q_, kv_cum)
		# (N * h, L, 2 * d) -> (N * h, L, 2 * d)
		k_cum = torch.cumsum(k_, dim=1)
		# (N * h, L, 2 * d) (N * h, L, 2 * d) -> (N * h, L)
		denom = torch.clamp_min(torch.einsum("nlm,nlm->nl", q_, k_cum), eps)
		# (N * h, L, d) (N * h, L, 1) -> (N * h, L, d)
		attn_output = qkv / denom.unsqueeze(-1)
		# (N * h, L, d) -> (N, h, L, d)
		attn_output = attn_output.view(bsz, num_heads, tgt_len, head_dim)

		# attn_output is shape of [batch_size, head, length, d_tensor]
		return attn_output

	def forward(self, q, k, v, mask=None):
		# input is 4 dimension tensor
		# [batch_size, head, length, d_tensor]
		batch_size, head, length, d_tensor = k.size()

		# 1. apply ReLU to all Q, K, and V
		q = torch.nn.functional.relu(q)
		k = torch.nn.functional.relu(k)
		v = torch.nn.functional.relu(v)

		# 2. split using diag attention strategy
		w = self.block_size
		num_blocks = length // w
		q_blocks = torch.split(q, w, dim=2)  # list of [batch_size, head, w, d_tensor]
		k_blocks = torch.split(k, w, dim=2)  # list of [batch_size, head, w, d_tensor]
		v_blocks = torch.split(v, w, dim=2)  # list of [batch_size, head, w, d_tensor]
		score = torch.zeros(batch_size, head, length, d_tensor).to(q.device)

		# 3. cos reweighting
		for i in range(num_blocks):
			score_block = self.cos_reweight(q_blocks[i], k_blocks[i], v_blocks[i])
			score[:, :, i * w: (i + 1) * w, :] = score_block

		# 4. apply masking (opt)

		return score
