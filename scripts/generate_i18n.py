#!/usr/bin/env python

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import codecs
import csv
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
from glob import glob

NC = "\033[0m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
PINK = "\033[1;35m"
YELLOW = "\033[0;33m"


def error(msg):
    print(f"{RED}{msg}{NC}")


def warn(msg):
    print(f"{YELLOW}{msg}{NC}")


def info(msg, bold=False, end="\n"):
    color = PINK if bold else NC
    print(f"{color}{msg}{NC}", end=end)


def walk_on_values(obj, action):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                walk_on_values(v, action)
            else:
                action(obj, k, v)
    elif isinstance(obj, list):
        for item in obj:
            walk_on_values(item, action)


def translate_phrase(phrase, src_lang, dest_lang):
    """
    Translate a single phrase to dest language. e.g. use Google translate API.
    Here is an example of using mymemory api (https://mymemory.translated.net/doc/spec.php)
    """
    try:
        # in order to avoid using requests (hence using dependencies), use subprocess with cURL
        url_phrase = urllib.parse.quote(phrase)
        translation_api = f"'https://api.mymemory.translated.net/get?q={url_phrase}&langpair={src_lang}|{dest_lang}'"
        response = subprocess.run(
            f"curl {translation_api}", shell=True, capture_output=True
        ).stdout
        data = json.loads(response)
        if "responseData" in data:
            if "match" in data["responseData"] and data["responseData"]["match"] > 0.1:
                return data["responseData"]["translatedText"], True

        return phrase, False
    except:
        return phrase, False


def collect_strings(json_files):
    closed_strings_list = set()

    for src_file in json_files:
        last_count = len(closed_strings_list)
        translation_obj = json.loads(open(src_file, "r").read())
        walk_on_values(
            translation_obj, lambda _, __, value: closed_strings_list.add(value)
        )
        diff_count = len(closed_strings_list) - last_count
        info(f"      🐍 file {src_file} contains {diff_count} new strings")
    return closed_strings_list


def translate_all(strings_list, src_lang, dest_lang):
    translations = {}
    total_strings = len(strings_list)
    translated = 0
    not_translated = []
    for phrase in strings_list:
        translations[phrase], success = translate_phrase(phrase, src_lang, dest_lang)
        if success:
            translated += 1
        else:
            not_translated.append(phrase)
        info(
            f"      🧮 translated {translated} out of {total_strings} strings ({len(not_translated)} failed)",
            end="\r",
        )
    info("")
    if len(not_translated):
        printable_not_translated = "\n".join(not_translated)
        warn(f"      ⚠️ did not translate the following: {printable_not_translated}")

    return translations


def process_lang(
    src_dir, src_lang, dest_lang, dest_dir, input_file, auto_translate, csv_dest_file
):
    info("  🤓 collecting strings...", bold=True)
    json_files = glob(os.path.join(src_dir, "**", "*.json"), recursive=True)
    closed_strings_list = collect_strings(json_files)
    translations = {}

    if csv_dest_file:
        info(f"  🤓 dumping {dest_lang} locale to {csv_dest_file}...", bold=True)
        csv_lines = [f"source (english), translation{os.linesep}"]
        for phrase in closed_strings_list:
            escaped = phrase.replace('"', '""')
            csv_lines.append(f'"{escaped}", {os.linesep}')
        open(csv_dest_file, "w").writelines(csv_lines)

    if auto_translate:
        info(f"  🤓 translating from {src_lang} to {dest_lang}...", bold=True)
        translations = translate_all(closed_strings_list, src_lang, dest_lang)
    if input_file:
        with open(input_file, "r") as infile:
            input_file_content = csv.reader(infile)
            for phrase, translation in list(input_file_content)[
                1:
            ]:  # skip the header row
                translations[phrase] = translation

    if input_file or auto_translate:
        info(f"  🤓 dumping {dest_lang} locale to {dest_dir}...", bold=True)
        create_new_locale(dest_dir, json_files, translations)
        shutil.copy(
            os.path.join(src_dir, "index.ts"), os.path.join(dest_dir, "index.ts")
        )


def create_new_locale(dest_dir, json_files, translations):
    def update_value(obj, key, value):
        obj[key] = translations[value]

    for src_file in json_files:
        dest_filename = os.path.basename(src_file)
        dest_file = os.path.join(dest_dir, dest_filename)
        translation_obj = json.loads(open(src_file, "r").read())
        walk_on_values(translation_obj, update_value)
        with codecs.open(dest_file, "w", "utf-8") as f:
            f.write(json.dumps(translation_obj, indent=2, ensure_ascii=False))
            info(f"      🐍 file {dest_file} written successfully")


def run():
    parser = argparse.ArgumentParser(
        description="Generate a new scaffold for a new translation language based on another existed language"
    )
    parser.add_argument(
        "-s",
        "--source",
        help="source language to generate the new one from",
        required=True,
    )
    parser.add_argument("-d", "--destination", help="language symbol to generate")
    parser.add_argument(
        "-a",
        "--auto-translate",
        action="store_true",
        help="run auto translation engine",
    )
    parser.add_argument(
        "-e", "--export", help="output file of exported string list for translation"
    )
    parser.add_argument(
        "-i", "--input", help="translated file to create the new language files from"
    )

    args = parser.parse_args()
    current = os.getcwd()
    locales_dir = os.path.join(current, "frontend", "backend", "locales")
    source_dir = os.path.join(locales_dir, args.source)
    translation_dest_dir = None
    csv_dest_file = None
    translation_dest_dir = os.path.join(locales_dir, args.destination)
    if args.export is not None:
        if os.path.isdir(args.export):
            error(
                f"❗export can't be made to a directory {args.export} please use a file as an argument"
            )
            sys.exit(-1)
        csv_dest_file = args.export
        if not csv_dest_file.endswith(".csv"):
            csv_dest_file = f"{csv_dest_file}.csv"
    if args.input is not None:
        if args.auto_translate:
            error(
                f"❗using input file and auto translation features together is not allowed"
            )
            sys.exit(-1)

        if os.path.isdir(args.input) or not os.path.exists(args.input):
            error(f"❗input translation file does not exists or is not a file")
            sys.exit(-1)

    if not os.path.exists(source_dir):
        error(f"❗could not find locale {args.source} at {source_dir}")
        sys.exit(-1)

    info(
        f"👷 Generating a new i18n translation language {args.destination} files...",
        bold=True,
    )
    process_lang(
        src_dir=source_dir,
        src_lang=args.source,
        dest_lang=args.destination,
        dest_dir=translation_dest_dir,
        auto_translate=args.auto_translate,
        input_file=args.input,
        csv_dest_file=csv_dest_file,
    )

    step = 1
    info(f"👷 Translation language {args.destination} files are ready", bold=True)
    info("    Next steps:")
    if csv_dest_file:
        info(f"      {step}. translate all strings in the csv file: {csv_dest_file}")
        step += 1
        info(
            f"      {step}. use this script again with {csv_dest_file} as -i (or --input) argument"
        )
        step += 1
    if translation_dest_dir:
        info(
            f'      {step}. add `import {args.destination.upper()} from "./{args.destination}";` to frontend/backend/locales/index.ts'
        )
        step += 1
        info(
            f"      {step}. add `{args.destination}: {args.destination.upper()};` to the default Resource object in there"
        )


if __name__ == "__main__":
    run()
