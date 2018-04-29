from keras import backend as K
import numpy as np
import keras
import editdistance
import csv
import os
from spell import Spell

def labels_to_text(labels):
    # 26 is space, 27 is CTC blank char
    text = ''
    for c in labels:
        if c >= 0 and c < 26:
            text += chr(c + ord('a'))
        elif c == 26:
            text += ' '
    return text

def decode(y_pred, input_length, greedy=False, beam_width=10, top_paths=1):
    """Decodes the output of a softmax.
    Can use either greedy search (also known as best path)
    or a constrained dictionary search.
    # Arguments
        y_pred: tensor `(samples, time_steps, num_categories)`
            containing the prediction, or output of the softmax.
        input_length: tensor `(samples, )` containing the sequence length for
            each batch item in `y_pred`.
        greedy: perform much faster best-path search if `true`.
            This does not use a dictionary.
        beam_width: if `greedy` is `false`: a beam search decoder will be used
            with a beam of this width.
        top_paths: if `greedy` is `false`,
            how many of the most probable paths will be returned.
    # Returns
        Tuple:
            List: if `greedy` is `true`, returns a list of one element that
                contains the decoded sequence.
                If `false`, returns the `top_paths` most probable
                decoded sequences.
                Important: blank labels are returned as `-1`.
            Tensor `(top_paths, )` that contains
                the log probability of each decoded sequence.
    """
    decoded = K.ctc_decode(y_pred=y_pred, input_length=input_length,
                           greedy=greedy, beam_width=beam_width, top_paths=top_paths)
    paths = [path.eval(session=K.get_session()) for path in decoded[0]]
    #logprobs  = decoded[1].eval(session=K.get_session())
    spell = Spell(path='grid.txt')
    preprocessed = [labels_to_text, spell.sentence]
    for output in paths[0]:
        out = output
        for postprocessor in self.postprocessors:
            out = postprocessor(out)
        preprocessed.append(out)

    return preprocessed


class Statistics(keras.callbacks.Callback):
    def __init__(self, model, x_train, y_train, input_len_train, label_len_train, num_samples_stats=256, output_dir=None):
        self.model = model
        self.x_train = x_train
        self.y_train = y_train
        self.input_length = input_length
        self.label_length = label_length
        self.output_dir = output_dir
        self.num_sample_stats = num_samples_stats
        if output_dir is not None and not os.path.exist(output_dir):
            os.make_dir(self.output_dir)


    def get_statistics(self, num):
        num_left = num
        data = []
        source_str = []

        while num_left > 0:
            input_data = {'the_input': self.x_train[0:num_proc], 'the_labels': self.y_train[0:num_proc],
             'label_length': label_len_train[0:num_proc], 'input_length': input_len_train[0:num_proc]}
            num_proc        = min(x_train.shape[0], num_left)
            y_pred = K.function([input_data, K.learning_phase()], [0])
            input_length    = self.input_length[0:num_proc]
            decoded_res     = decode(y_pred, input_length)
            for i in range(0, num_proc):
                source_str.append(labels_to_text(self.y_train[i]))
            for j in range(0, num_proc):
                data.append((decoded_res[j], source_str[j]))

            num_left -= num_proc

        mean_cer, mean_cer_norm    = self.get_mean_character_error_rate(data)
        mean_wer, mean_wer_norm    = self.get_mean_word_error_rate(data)

        return {
            'samples': num,
            'cer': (mean_cer, mean_cer_norm),
            'wer': (mean_wer, mean_wer_norm),
        }

    def get_mean_character_error_rate(self, data):
        mean_individual_length = np.mean([len(pair[1]) for pair in data])
        return self.get_mean_tuples(data, mean_individual_length, editdistance.eval)

    def get_mean_word_error_rate(self, data):
        mean_individual_length = np.mean([len(pair[1].split()) for pair in data])
        return self.get_mean_tuples(data, mean_individual_length, wer_sentence)


    def on_train_begin(self, logs={}):
        with open(os.path.join(self.output_dir, 'stats.csv'), 'wb') as csvfile:
            csvw = csv.writer(csvfile)
            csvw.writerow(
                ["Epoch", "Samples", "Mean CER", "Mean CER (Norm)", "Mean WER", "Mean WER (Norm)"])

    def on_epoch_end(self, epoch, logs={}):
        stats = get_statistics(self, self.num_sample_stats)
        print('\n\n[Epoch %d] Out of %d samples: [CER: %.3f - %.3f] [WER: %.3f - %.3f] \n'
              % (epoch, stats['samples'], stats['cer'][0], stats['cer'][1], stats['wer'][0], stats['wer'][1]))