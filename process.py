from __future__ import print_function

import argparse
import datetime
import glob
import os
import itertools
import shutil
import subprocess
import string

from merge_alignments import merge

from treetagger_xml.xml import process_single
from treetagger_xml.utils import instantiate_tagger


def preprocess(languages, languages_dirs):
    """
    Preprocesses all files for a language
    :param languages: the current languages
    :param languages_dirs: the current directories per language
    """
    for language in languages:
        for filename in glob.glob(os.path.join(languages_dirs[language], '*.txt')):
            preprocess_single(language, filename)


def preprocess_single(language, filename):
    """
    Preprocess: a single file
    - Remove lines before (and including) the date of the article.
    - Remove lines when the attachments start
    - Add paragraph breaks when a potential title is encountered

    :param language: the current language
    :param filename: the current filename
    """
    lines = []
    with open(filename, 'rb') as f:
        look_for_date = True
        for line in f:
            line = line.strip()

            if look_for_date:
                try:
                    # A date looks like 2011-07-05 - 13:39
                    datetime.datetime.strptime(line, '%Y-%m-%d - %H:%M')
                    look_for_date = False
                    continue
                except ValueError:
                    continue
            else:
                # Check for stop conditions
                if line[:8].isdigit():
                    # We might have run into another date:
                    try:
                        datetime.datetime.strptime(line[:8], '%Y%m%d')
                        # If this is indeed a date, stop here.
                        break
                    except ValueError:
                        continue
                if line == language.upper() or line.startswith('-//'):
                    # Definitely stop if a line consisting of only the language is found, or it starts with '-//'
                    break

                # Check for titles
                if not line.endswith(tuple(string.punctuation)):
                    lines.append('')

                lines.append(line)

    new_filename = os.path.splitext(filename)[0] + '.prep'
    with open(new_filename, 'wb') as f:
        f.write('\n'.join(lines))


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
    languages_dirs = create_output_dirs(languages, output_dir)

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


def merge_alignments(output_dir, languages):
    """
    Merges the created alignments into a single file
    :param output_dir: the output directory (where all output is stored)
    :param languages: the current languages
    """
    comb_ls = itertools.combinations(sorted(languages), 2)
    for sl, tl in comb_ls:
        # Merge alignment files
        alignments = glob.glob(os.path.join(output_dir, '{sl}-{tl}-*.xml'.format(sl=sl, tl=tl)))
        merged_file = os.path.join(output_dir, '{sl}-{tl}.xml'.format(sl=sl, tl=tl))
        merge(alignments, merged_file)

        # Remove individual alignment files
        for alignment in alignments:
            os.remove(alignment)


def sentence_align(input_dir, output_dir, languages, languages_dirs):
    """
    Applies sentence alignment (using hunalign) to the DCEP corpus
    :param input_dir: the input directory (will remain untouched)
    :param output_dir: the output directory (where all output is stored)
    :param languages: the current languages
    :param languages_dirs: the current directories per language
    """
    # Look up the translations
    translations = dict()
    comb_ls = itertools.combinations(sorted(languages), 2)

    for comb_l in comb_ls:
        with open(os.path.join(input_dir, 'indices', '-'.join(comb_l).upper()), 'rb') as f:
            for line in f:
                _, src, trg = line.split('\t')
                src = os.path.splitext(os.path.basename(src))[0]
                trg = os.path.splitext(os.path.basename(trg))[0]
                translations[src] = trg

        sl = comb_l[0]
        tl = comb_l[1]
        for i, src in enumerate(glob.glob(os.path.join(languages_dirs[sl], '*.xml'))):
            src_lookup = os.path.splitext(os.path.basename(src))[0]

            try:
                trg_lookup = translations[src_lookup]
            except KeyError:
                print('File {} not found in the indices file'.format(src_lookup))
                continue

            src = os.path.join(*(src.split(os.path.sep)[1:]))  # Removes the first folder in the path, see https://stackoverflow.com/a/26724413
            trg = os.path.join(tl, trg_lookup + '.xml')
            if not os.path.exists(os.path.join(output_dir, trg)):
                print('Translation for {} ({}) not found'.format(src_lookup, trg))
                continue

            # Create alignment files
            command = 'uplug align/hun -src {src} -trg {trg} -s {sl} -t {tl}'.format(src=src, trg=trg, sl=sl, tl=tl)
            out_file = os.path.join(output_dir, '{sl}-{tl}-{i}.xml'.format(sl=sl, tl=tl, i=i))
            with open(out_file, 'wb') as out:
                subprocess.call(command, stdout=out, shell=True, cwd=output_dir)


def create_output_dirs(languages, output_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # Make dirs per language
    languages_dirs = dict()
    for language in languages:
        language_dir = os.path.join(output_dir, language)
        if not os.path.exists(language_dir):
            os.mkdir(language_dir)
        languages_dirs[language] = language_dir
    return languages_dirs


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
