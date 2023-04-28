class Config:
    USE_GPU = True
    NUM_EPOCHS = 1
    TRAIN_SEQ_LENGTH = 150
    TEST_SEQ_LENGTH = 450
    BATCH_SIZE = 200
    LSTM_HIDDEN_SIZE = 300
    LSTM_EMBEDDING_SIZE = 300
    LSTM_NUM_LAYERS = 1
    LSTM_DROUPOUT = 0
    LEARNING_RATE = 0.001
    UPSAMPLE_NEGATIVE = True
    UPSAMPLE_RATIO = 2  # 1 means no upsampling
