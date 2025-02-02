import numpy as np
import torch
import torch.nn as nn

import os


class MyLSTM(torch.nn.Module):
    def __init__(self, Config, vocab_size, num_classes, device):
        super(MyLSTM, self).__init__()
        self.num_layers = Config.LSTM_NUM_LAYERS
        self.hidden_size = Config.LSTM_HIDDEN_SIZE

        if Config.WORD_EMBEDDING == 'custom':
            # Train embeddings from scratch
            self.embedding_size = Config.LSTM_EMBEDDING_SIZE
            self.embedding = nn.Embedding(
                vocab_size, self.embedding_size, padding_idx=0)
        elif Config.WORD_EMBEDDING == 'glove':
            # Use pretrained GloVe embeddings
            import torchtext
            self.embedding_size = Config.GLOVE_EMBEDDING_SIZE
            glove = torchtext.vocab.GloVe(
                name='6B', dim=self.embedding_size, cache=Config.GLOVE_CACHE_DIR)
            print(f"Loading GloVe embeddings of shape: {glove.vectors.shape}")
            self.embedding = torch.nn.Embedding.from_pretrained(
                glove.vectors, freeze=True)
        elif Config.WORD_EMBEDDING == 'paragramcf':
            self.embedding_size = 300
            word_embeddings_file = os.path.join(
                Config.PARAGRAMCF_DIR, "paragram.npy")
            paragramcf = torch.from_numpy(np.load(word_embeddings_file))
            print(f"Loading Paragram embeddings of shape: {paragramcf.shape}")
            self.embedding = nn.Embedding.from_pretrained(
                paragramcf, freeze=True)

        self.lstm = torch.nn.LSTM(
            self.embedding_size, self.hidden_size, self.num_layers,
            batch_first=True, bidirectional=True, dropout=Config.LSTM_DROUPOUT)
        self.fc = torch.nn.Linear(self.hidden_size*2, num_classes)
        self.device = device

    def forward(self, x):
        # For unbatched 1D input, we add a batch dimension of 1
        if len(x.shape) == 1:
            x = x.unsqueeze(0)
            batch_size = 1
        elif len(x.shape) == 2:
            batch_size = x.shape[0]
        else:
            raise ValueError(
                "Input must be a 1D or 2D tensor. Got tensor of shape: {}".format(x.shape))
        # x shape (batch_size, seq_length)
        x = x.long()
        x = self.embedding(x)  # (batch_size, seq_length, embedding_size)

        # h0, c0 shape (num_layers*2, batch_size, hidden_size)
        # Set initial states
        h0 = torch.zeros(self.num_layers*2, batch_size,
                         self.hidden_size).to(self.device)
        c0 = torch.zeros(self.num_layers*2, batch_size,
                         self.hidden_size).to(self.device)

        # Forward propagate LSTM
        # out: tensor of shape (batch_size, seq_length, hidden_size*2)
        out, _ = self.lstm(x, (h0, c0))

        # Decode the hidden state of the last time step
        out = out[:, -1, :]
        # out shape (batch_size, hidden_size*2)
        out = self.fc(out)  # (batch_size, num_classes)
        return out

# TODO LSTM with attention?
