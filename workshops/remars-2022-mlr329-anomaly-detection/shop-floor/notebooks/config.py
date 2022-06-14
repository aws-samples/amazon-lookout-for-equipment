# Update the name of the bucket you want to use
# to store the intermediate results of this getting
# started:

BUCKET                   = 'pump-anomaly-detection'
EQUIPMENT                = 'water-pump'

# You can leave these other parameters to these
# default values:

PREFIX_TRAINING          = f'training-data/'
PREFIX_LABEL             = f'label-data/'
PREFIX_INFERENCE         = f'inference-data'
DATASET_NAME             = f'{EQUIPMENT}'
MODEL_NAME               = f'{DATASET_NAME}-model'
INFERENCE_SCHEDULER_NAME = f'{DATASET_NAME}-scheduler'