

import numpy as np
import argparse
from parse_data_from_log import DataLogParser
from data_preprocessing import DataPreprocess
from data_learning import NeuralNetworkModel
import train_test_conf as conf



def get_input_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', help="if Y, run under training mode, if N run under test mode", type=str,
                        default='Y')
    args = parser.parse_args()
    return args


def main():
    args = get_input_arguments()
    training_mode = (args.mode == 'Y')
    if args.mode not in ['Y', 'N']:
        raise ValueError('Invalid input value for m should be either Y or N')
    data_folder = conf.data_folder
    if training_mode:
        label = conf.train_label
        print('in training mode')
        print('training data from {} \nvalidation data from {}\n'.format(conf.training_date, conf.training_validate_date))
        print('training label is {}\n'.format(label))
        data_folder += "training/"
    else:
        label = conf.test_label
        print('in test mode')
        print('test date from {}'.format(conf.test_date))
        print('test label is {}\n'.format(label))
        data_folder += "test/"
   
    print("parsing data from log files which are generated by Atheros-CSI-TOOL\n")
    data_generator = DataLogParser(conf.n_timestamps, conf.D, conf.step_size,
                                   conf.ntx_max, conf.nrx_max, conf.nsubcarrier_max,
                                   data_folder, conf.log_folder,
                                   conf.skip_frames,
                                   conf.time_offset_ratio,
                                   conf.day_conf,
                                   label)
    train_date = conf.training_date if training_mode else []
    if training_mode:
        data_generator.generate_image(conf.training_date, conf.training_validate_date)
    else:
        data_generator.generate_image([], conf.test_date)    
    train_data, test_data = data_generator.get_data()

  
    print("Pre-processing data\n")
    data_process = DataPreprocess(conf.n_timestamps, conf.D, conf.step_size,
                                  conf.ntx_max, conf.ntx, conf.nrx_max,
                                  conf.nrx, conf.nsubcarrier_max, conf.nsubcarrier,
                                  conf.data_shape_to_nn,
                                  data_folder, label)
    data_process.load_image(training_mode, False, train_data, test_data)
    data_process.signal_processing(conf.do_fft, conf.fft_shape)
    data_process.prepare_shape()
    x_train, y_train, x_test, y_test = data_process.get_data()
    
    nn_model = NeuralNetworkModel(conf.data_shape_to_nn, conf.abs_shape_to_nn,
                                  conf.phase_shape_to_nn, conf.total_classes)
    nn_model.add_data(x_train, y_train, x_test, y_test)
    if training_mode:
        print("Building a new model (in training mode)\n")
        nn_model.cnn_model_abs_phase()
        nn_model.fit_data(conf.epochs)
        nn_model.save_model(conf.model_name)
    else:
        print("Get test result using existing model (in test mode)\n")
        nn_model.load_model(conf.model_name)
        result = nn_model.get_test_result(label)
        
    nn_model.end()
    print("Done!")


if __name__ == "__main__":
    main()