import os


def create_output_dirs(output_dir, languages):
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
