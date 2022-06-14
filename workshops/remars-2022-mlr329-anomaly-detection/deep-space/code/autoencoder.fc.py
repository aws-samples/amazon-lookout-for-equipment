import argparse, os
import numpy as np
import pandas as pd

import tensorflow as tf
import tensorflow.keras as keras
from tensorflow.keras.layers import Input, Dense, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras import regularizers
from tensorflow.keras.utils import multi_gpu_model

if __name__ == '__main__':
        
    parser = argparse.ArgumentParser()

    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--learning-rate', type=float, default=0.001)
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--activation', type=str, default="relu")
    parser.add_argument('--dropout', type=float, default=0.0)
    parser.add_argument('--gpu-count', type=int, default=os.environ['SM_NUM_GPUS'])
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--training', type=str, default=os.environ['SM_CHANNEL_TRAINING'])
    parser.add_argument('--validation', type=str, default=os.environ['SM_CHANNEL_VALIDATION'])
    args, _ = parser.parse_known_args()
    
    # read in data
    x_train = np.load(os.path.join(args.training, 'training.npz'))['train']
    x_val = np.load(os.path.join(args.validation, 'validation.npz'))['validation']
        
    # build network 
    input_dim = x_train.shape[1]

    input_layer = Input(shape=(input_dim, ))
    
    #encoder = Dense(200, activation=args.activation,activity_regularizer=regularizers.l1(args.learning_rate))(input_layer)
    encoder = Dense(200, activation=args.activation)(input_layer)
    encoder = Dense(50, activation=args.activation)(encoder)
    encoder = Dense(50, activation=args.activation)(encoder)
    encoder = Dropout(args.dropout)(encoder)
    encoder = Dense(10, activation=args.activation)(encoder)
    encoder = Dropout(args.dropout)(encoder)   
    decoder = Dense(50, activation=args.activation)(encoder)
    decoder = Dense(50, activation=args.activation)(decoder)
    decoder = Dense(200, activation=args.activation)(decoder)
    decoder = Dense(input_dim, activation=None)(decoder)
    
    autoencoder = Model(inputs=input_layer, outputs=decoder)
    print(autoencoder.summary())
    
    if args.gpu_count > 1:
        autoencoder = multi_gpu_model(autoencoder, gpus=args.gpu_count)
    
    # compile and fit 
    autoencoder.compile(optimizer='adam', loss='mean_squared_error')

    autoencoder.fit(x_train, x_train,
                    epochs=args.epochs,
                    batch_size=args.batch_size,
                    shuffle=True,
                    verbose=2,
                    validation_data=(x_val, x_val))
        
    score = autoencoder.evaluate(x_val, x_val,verbose=0)
    print('Validation loss    :', score)
    
    # Save the trained model:
    os.makedirs(os.path.join(args.model_dir, 'model/1'), exist_ok=True)
    autoencoder.save(os.path.join(args.model_dir, 'model/1'))
    