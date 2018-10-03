from __future__ import print_function

import argparse
import glob
import os
import shutil
import subprocess

from treetagger_xml.xml import process_single
from treetagger_xml.utils import instantiate_tagger

from preprocess import preprocess_single
from align import merge_alignments, sentence_align
from utils import create_output_dirs


def process(input_dir, output_dir, languages, fetch_limit, input_filter):
    """
    Processes the DCEP-corpus and converts it to the proper OPUS format
    :param input_dir: the input directory (will remain untouched)
    :param output_dir: the output directory (where all output is stored)
    :param languages: the languages for which to extract data
    :param fetch_limit: the maximum number of documents (per document type) to extract
    :param input_filter: the document types to extract
    """
    print('Creating language directories...')
    languages_dirs = create_output_dirs(output_dir, languages)

    print('Fetching raw .txt-files...')
    fetch_raw(input_dir, languages, languages_dirs, fetch_limit, input_filter)

    print('Preprocessing .txt-files...')
    preprocess(languages, languages_dirs)

    print('Tokenizing .txt-files into .xml-files...')
    tokenize(languages, languages_dirs)

    print('Applying TreeTagger...')
    treetag(languages, languages_dirs)

    print('Aligning on sentence-level...')
    sentence_align(input_dir, output_dir, languages, languages_dirs)

    print('Merging the alignments...')
    merge_alignments(output_dir, languages)


def preprocess(languages, languages_dirs):
    """
    Preprocesses all files for a language
    :param languages: the current languages
    :param languages_dirs: the current directories per language
    """
    for language in languages:
        for filename in glob.glob(os.path.join(languages_dirs[language], '*.txt')):
            preprocess_single(language, filename)


def treetag(languages, languages_dirs):
    """
    Adds part-of-speech-tags and lemmatization to .xml-files
    :param languages: the current languages
    :param languages_dirs: the current directories per language
    """
    for language in languages:
        tagger = instantiate_tagger(language)
        for src in glob.glob(os.path.join(languages_dirs[language], '*.xml')):
            process_single(tagger, language, src, in_place=True)


def tokenize(languages, languages_dirs):
    # Tokenize and convert to XML
    for language in languages:
        for filename in glob.glob(os.path.join(languages_dirs[language], '*.prep')):
            f = os.path.splitext(filename)[0]
            command = 'uplug -f pre/basic pre/{language}/basic -in {f}.prep > {f}.xml'.format(language=language, f=f)
            subprocess.call(command, shell=True, stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT)


def fetch_raw(input_dir, languages, languages_dirs, fetch_limit, input_filter):
    # Grab the raw text files
    for language in languages:
        in_dir = os.path.join(os.path.join(input_dir, 'sentence/xml'), language.upper())
        source_dirs = os.listdir(in_dir)
        if input_filter:
            source_dirs = input_filter

        for source_dir in source_dirs:
            n = 0
            for filename in glob.glob(os.path.join(in_dir, source_dir, '*.txt')):
                shutil.copy(filename, languages_dirs[language])
                n += 1
                if fetch_limit and n == fetch_limit:
                    break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert DCEP files to OPUS format (.xml)')
    parser.add_argument('dcep_location', help='DCEP location')
    parser.add_argument('output_location', help='Output location')
    parser.add_argument('--languages', nargs='+', help='Languages to select')
    parser.add_argument('--limit', type=int, default=0, help='Number of documents to select')
    parser.add_argument('--filter', nargs='*', help='Filter on the type of documents to convert')

    args = parser.parse_args()

    process(args.dcep_location, args.output_location, args.languages, args.limit, args.filter)
