# -*- coding: utf-8 -*-
"""
@date: 2020.1.10
@author: liluoqin
@function:
    process pretreatment data
"""
import os
import errno
import sentencepiece as spm
import re
import logging
import jieba
import sys
from sklearn.model_selection import train_test_split
sys.path.append("..")

from hparams import Hparams
logging.basicConfig(level=logging.INFO)
file_path = os.path.dirname(__file__)


def prepro(hp):

    barrages_data = os.path.join(file_path, '..', hp.barrages_data)

    # train
    _prepro = lambda x: [line.split("\t")[0] for line in open(x, 'r', encoding="utf-8").readlines()
                         if not line.startswith("barrage")]

    def _write(sents, fname):
        with open(fname, 'w', encoding="utf-8") as fout:
            fout.write("\n".join(sents))

    logging.info("# Preprocessing")
    prepro_sents = _prepro(barrages_data)

    logging.info("# write preprocessed files to disk")
    os.makedirs("../barrages_data/prepro", exist_ok=True)

    # split data
    train_x, test_x, train_y, test_y = train_test_split(prepro_sents, prepro_sents, test_size=0.2)

    _write(prepro_sents, "../barrages_data/prepro/all_sents.txt")
    _write(train_x, "../barrages_data/prepro/train_x.txt")
    _write(train_y, "../barrages_data/prepro/train_y.txt")
    _write(test_x, "../barrages_data/prepro/test_x.txt")
    _write(test_y, "../barrages_data/prepro/test_y.txt")

    logging.info("# Train a joint BPE model with sentencepiece")
    os.makedirs("../barrages_data/segmented", exist_ok=True)
    train = '--input=../barrages_data/prepro/all_sents.txt --pad_id=0 --unk_id=1 \
                 --bos_id=2 --eos_id=3\
                 --model_prefix=../barrages_data/segmented/bpe --vocab_size={} \
                 --model_type=bpe'.format(hp.vocab_size)
    spm.SentencePieceTrainer.Train(train)

    logging.info("# Load trained bpe model")
    sp = spm.SentencePieceProcessor()
    sp.Load("../barrages_data/segmented/bpe.model")

    logging.info("# Segment")

    def _segment_and_write(sents, fname):
        with open(fname, "w", encoding="utf-8") as fout:
            for sent in sents:
                pieces = sp.EncodeAsPieces(sent)
                fout.write(" ".join(pieces) + "\n")

    _segment_and_write(train_x, "../barrages_data/segmented/train_x.bpe")
    _segment_and_write(train_y, "../barrages_data/segmented/train_y.bpe")
    _segment_and_write(test_x, "../barrages_data/segmented/test_x.bpe")
    _segment_and_write(test_y, "../barrages_data/segmented/test_y.bpe")

    logging.info("# Let's see how segmented data look like")
    print("train:", open("../barrages_data/segmented/train_x.bpe", 'r', encoding="utf-8").readline())
    print("test:", open("../barrages_data/segmented/test_x.bpe", 'r', encoding="utf-8").readline())


if __name__ == "__main__":
    hparams = Hparams()
    parser = hparams.parser
    hp = parser.parse_args()
    prepro(hp)
    logging.info("# Done")