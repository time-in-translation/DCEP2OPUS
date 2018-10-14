from __future__ import print_function

import argparse
import glob
import os
import subprocess

import itertools

from merge_alignments import merge
from utils import create_output_dirs


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
        merge(alignments, merged_file, delete_files_in=True)


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

            trg = os.path.join(output_dir, os.path.join(tl, trg_lookup + '.xml'))
            if not os.path.exists(trg):
                print('Translation for {} ({}) not found'.format(src_lookup, trg))
                continue

            # Create alignment files
            command = 'uplug align/hun -src {src} -trg {trg} -s {sl} -t {tl}'.format(src=src, trg=trg, sl=sl, tl=tl)
            out_file = os.path.join(output_dir, '{sl}-{tl}-{i}.xml'.format(sl=sl, tl=tl, i=i))
            with open(out_file, 'wb') as out:
                subprocess.call(command, stdout=out, stderr=open(os.devnull, 'w'), shell=True, cwd=output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help='Input files')
    parser.add_argument('output_dir', help='Output file')
    parser.add_argument('languages', nargs='+', help='Languages')
    args = parser.parse_args()

    languages_dirs = create_output_dirs(args.output_dir, args.languages)
    sentence_align(args.input_dir, args.output_dir, args.languages, languages_dirs)
    merge_alignments(args.output_dir, args.languages)
