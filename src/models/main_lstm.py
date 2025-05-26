from smiles_featurizers import mac_keys_fingerprints, one_hot_encode, morgan_fingerprints_mac_and_one_hot
import pandas as pd
import argparse
import os
from lstm import SwiftDock
from swift_dock_logger import swift_dock_logger
import time

logger = swift_dock_logger()

training_metrics_dir = '../../results/validation_metrics/'
testing_metrics_dir = '../../results/testing_metrics/'
test_predictions_dir = '../../results/test_predictions/'
project_info_dir = '../../results/project_info/'
serialized_models_path = '../../results/serialized_models/'
shap_analyses_dir = '../../results/shap_analyses/'
tsne_analyses_dir = '../../results/tsne_analyses/'
dataset_dir = "../../datasets/"
os.makedirs(training_metrics_dir, exist_ok=True)
os.makedirs(testing_metrics_dir, exist_ok=True)
os.makedirs(test_predictions_dir, exist_ok=True)
os.makedirs(project_info_dir, exist_ok=True)
os.makedirs(serialized_models_path, exist_ok=True)
os.makedirs(shap_analyses_dir, exist_ok=True)
os.makedirs(tsne_analyses_dir, exist_ok=True)


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def get_descriptor_data(descriptor):
    descriptors = {
        'mac': [167, mac_keys_fingerprints],
        'onehot': [3500, one_hot_encode],
        'morgan_onehot_mac': [4691, morgan_fingerprints_mac_and_one_hot]
    }
    return descriptors.get(descriptor, None)


def get_descriptor_name(func):
    descriptors = {
        'mac_keys_fingerprints': 'mac',
        'one_hot_encode': 'onehot',
        'morgan_fingerprints_mac_and_one_hot': 'morgan_onehot_mac'
    }
    return descriptors.get(func.__name__, None)


def train_models(args, target, descriptor_data, size):
    number_of_folds = 5
    identifier = f"lstm_{target}_{get_descriptor_name(descriptor_data[1])}_{size}"
    logger.info(f"Identifier {identifier}")
    identifier_data = f"{tsne_analyses_dir}{identifier}_data.csv"
    data_csv = f"{dataset_dir}{target}.csv"

    path_to_csv_file = f"../../datasets/{target}.csv"
    data_all = pd.read_csv(path_to_csv_file).dropna()
    data_all.to_csv(identifier_data, index=False)
    
    train_size = size
    val_size = size * (number_of_folds-1) if args.cross_validate else 0
    test_size = len(data_all) - (train_size + val_size)
    
    
    model = SwiftDock(
        training_metrics_dir, testing_metrics_dir, test_predictions_dir,
        project_info_dir, data_all, train_size, test_size, val_size, identifier,
        number_of_folds, descriptor_data[1], descriptor_data[0], serialized_models_path, args.cross_validate,
        shap_analyses_dir, tsne_analyses_dir, data_csv=data_csv)

    model.split_data(cross_validate=args.cross_validate)
    model.train()

    if args.cross_validate:
        model.diagnose()
    model.test()
    model.save_results()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="train code for fast docking",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", type=str, help="specify the target protein to", nargs='+')
    parser.add_argument("--descriptors", type=str, help="specify the training descriptor", nargs='+')
    parser.add_argument("--training_sizes", type=int, help="Training and cross validation size", nargs='+')
    parser.add_argument("--cross_validate", type=str2bool, help="If to use 5 cross validation")
    args = parser.parse_args()

    for target in args.input:
        for descriptor in args.descriptors:
            descriptor_data = get_descriptor_data(descriptor)
            if descriptor_data:
                for size in args.training_sizes:
                    start_time = time.time()
                    train_models(args, target, descriptor_data, size)
                    end_time = time.time()
                    duration = (end_time - start_time) / 60

                    print(f"Tempo total - {duration:.2f} minutos")

