import argparse
import datetime
import glob
import os
import itertools
import shutil
import subprocess
import string

from merge_alignments import merge


def preprocess(languages, languages_dirs):
    # Tokenize and convert to XML
    for language in languages:
        for filename in glob.glob(os.path.join(languages_dirs[language], '*.txt')):
            preprocess_single(language, filename)


def preprocess_single(language, filename):
    # Preprocess:
    # - Remove lines before (and including) the date of the article.
    # - Remove lines when the attachments start
    # - Add paragraph breaks when a potential title is encountered
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


def process(input_dir, output_dir, languages):
    languages_dirs = create_output_dirs(languages, output_dir)
    # fetch_raw(input_dir, languages, languages_dirs, 200)
    preprocess(languages, languages_dirs)
    # tokenize(languages, languages_dirs)
    # treetag()

    # sentence_align(input_dir, output_dir, languages, languages_dirs)
    # merge_alignments(output_dir, languages)


def merge_alignments(output_dir, languages):
    comb_ls = itertools.combinations(sorted(languages), 2)
    for sl, tl in comb_ls:
        # Merge alignment files
        alignments = glob.glob(os.path.join(output_dir, '{sl}-{tl}-*.xml'.format(sl=sl, tl=tl)))
        merged_file = os.path.join(output_dir, '{sl}-{tl}.xml'.format(sl=sl, tl=tl))
        merge(alignments, merged_file)

        # Remove individual files
        for alignment in alignments:
            os.remove(alignment)


def sentence_align(input_dir, output_dir, languages, languages_dirs):
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
            try:
                src_lookup = os.path.splitext(os.path.basename(src))[0]
                trg_lookup = translations[src_lookup]
            except KeyError:
                print 'File {} not found in the indices file'.format(src_lookup)
                continue

            src = os.path.join(*(src.split(os.path.sep)[1:]))  # Removes the first folder in the path, see https://stackoverflow.com/a/26724413
            trg = os.path.join(tl, trg_lookup + '.xml')
            if not os.path.exists(os.path.join(output_dir, trg)):
                print 'Translation for {} ({}) not found'.format(src_lookup, trg)
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
    for language in languages:
        for filename in glob.glob(os.path.join(languages_dirs[language], '*.prep')):
            f = os.path.splitext(filename)[0]
            command = 'uplug -f pre/basic pre/{language}/basic -in {f}.prep > {f}.xml'.format(language=language, f=f)
            subprocess.call(command, shell=True)


def fetch_raw(input_dir, languages, languages_dirs, limit=0):
    # Grab the raw text files
    in_dir = os.path.join(input_dir, 'sentence/xml')
    for language in languages:
        source_dir = os.path.join(in_dir, language.upper(), 'IM-PRESS')

        n = 0
        for filename in glob.glob(os.path.join(source_dir, '*.txt')):
            shutil.copy(filename, languages_dirs[language])
            n += 1
            if limit and n == limit:
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert DCEP files to OPUS format (.xml)')
    parser.add_argument('dcep_location', type=str, help='DCEP location')
    parser.add_argument('--languages', nargs='+', help='Languages to select')
    # parser.add_argument('dcep_filter', type=str, help='Filter on the type of documents to convert')
    parser.add_argument('output_location', type=str, help='Output location')
    args = parser.parse_args()

    process(args.dcep_location, args.output_location, args.languages)
