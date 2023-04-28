import argparse
import pickle
import pandas as pd
import torch
import torch.nn as nn
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader

from lstm.my_lstm import MyLSTM
from train_lstm import YelpReviewDataset
from config import Config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', type=str, required=True)
    parser.add_argument('--vocab', type=str, required=True)
    parser.add_argument('--model', type=str, required=True)

    args = parser.parse_args()

    device = torch.device(
        'cuda' if Config.USE_GPU and torch.cuda.is_available() else 'cpu')
    print('Using device:', device)
    if device.type == 'cuda':
        print(f'Device count: {torch.cuda.device_count()}')
        print(f'Current device index: {torch.cuda.current_device()}')
        print(f'Device name: {torch.cuda.get_device_name(0)}')
        print(
            f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3} GB')

    # load vocab
    with open(args.vocab, 'rb') as f:
        vocab = pickle.load(f)

    # load data
    df = pd.read_csv(args.csv)
    _, test_data = train_test_split(df, test_size=0.2, random_state=42)
    # Reset dataframe index so that we can use df.loc[idx, 'text']
    test_data = test_data.reset_index(drop=True)
    test_dataset = YelpReviewDataset(test_data, vocab, train=False)

    # get dataloader from dataset
    test_loader = DataLoader(test_dataset, batch_size=Config.BATCH_SIZE, shuffle=False)

    # load lstm model
    model = MyLSTM(vocab_size=len(vocab), embedding_size=Config.LSTM_EMBEDDING_SIZE,
                   hidden_size=Config.LSTM_HIDDEN_SIZE, num_layers=Config.LSTM_NUM_LAYERS,
                   dropout=Config.LSTM_DROUPOUT, num_classes=1, device=device).to(device)
    model.load_state_dict(torch.load(args.model))
    model.eval()

    criterion = nn.BCEWithLogitsLoss()
    # test
    with torch.no_grad():
        correct = 0
        total = 0
        total_loss = 0
        TP, FP, TN, FN = 0, 0, 0, 0
        print("Testing...")
        for data, labels in tqdm(test_loader):
            data = data.to(device)
            labels = labels.unsqueeze(1).to(device)
            outputs = model(data)

            loss = criterion(outputs, labels)
            total_loss += loss.item()

            predicted = torch.round(torch.sigmoid(outputs))
            total += labels.size(0)

            TP += ((predicted == 1) & (labels == 1)).sum().item()
            FP += ((predicted == 1) & (labels == 0)).sum().item()
            TN += ((predicted == 0) & (labels == 0)).sum().item()
            FN += ((predicted == 0) & (labels == 1)).sum().item()
        print(f"Accuracy: {(TP + TN) / total:.4f}")
        print(f"Test Loss: {total_loss / len(test_loader):.4f}")

    # print confusion matrix
    print(f"TP: {TP}, FP: {FP}, TN: {TN}, FN: {FN}")
