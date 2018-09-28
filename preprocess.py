import argparse
import datetime
import os
import re
import string

# Copied from https://emailregex.com/
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
# Phone numbers look like (+32) 2 28 41009 or ( +32 ) 2 28 44264
PHONE_REGEX = re.compile(r'\(\s*\+\d{2}\s*\)[\s\d]+')


def preprocess(language, file_names):
    for file_name in file_names:
        preprocess_single(language, file_name)


def preprocess_single(language, file_name):
    """
    Preprocesses a single file:
    - Remove lines before (and including) the date of the article.
    - Remove lines when the attachments start
    - Add paragraph breaks when a potential title is encountered

    :param language: the current language
    :param file_name: the current filename
    """
    lines = []
    with open(file_name, 'rb') as f:
        look_for_date = True
        i = 0
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

                # Check for e-mail addresses and phone numbers (first line only)
                if i == 0:
                    line = trim_from_last(EMAIL_REGEX, line)
                    line = trim_from_last(PHONE_REGEX, line)

                # Check for titles
                if not line.endswith(tuple(string.punctuation)):
                    lines.append('')

                lines.append(line)
                i += 1

    new_filename = os.path.splitext(file_name)[0] + '.prep'
    with open(new_filename, 'wb') as f:
        f.write('\n'.join(lines))


def trim_from_last(regex, line):
    if re.search(regex, line):
        for match in re.finditer(regex, line):
            last_match = match
        line = line[last_match.end():].strip()
    return line


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('language', help='Language')
    parser.add_argument('file_in', nargs='+', help='Input file')
    args = parser.parse_args()

    preprocess(args.language, args.file_in)
