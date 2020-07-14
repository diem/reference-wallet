# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0
import os

walk_dir = os.getcwd()

print('walk_dir = ' + os.path.abspath(walk_dir))

copyright_header_lines = [
    "Copyright (c) The Libra Core Contributors",
    "SPDX-License-Identifier: Apache-2.0"
]

exclude_dirs = ["node_modules", "thirdparty"]

extention_to_comment_prefix = {
    '.py': '#',
    '.sh': '#',
    '.ts': '//',
    '.tsx': '//'
}

for root, folder, files in os.walk(walk_dir, topdown=True):
    files = [f for f in files if not f[0] == '.']
    folder[:] = [f for f in folder if not f[0] == '.' and f not in exclude_dirs]

    for full_filename in files:

        filename, file_extension = os.path.splitext(full_filename)

        if file_extension in extention_to_comment_prefix.keys():
            comment_prefix = extention_to_comment_prefix[file_extension]
            file_path = os.path.join(root, full_filename)

            with open(file_path, 'r+') as f:
                content = f.read()
                if copyright_header_lines[0] not in content:
                    print(f'\t- patching {file_path}')
                    f.seek(0, 0)
                    f.writelines([f'{comment_prefix} {line}\n' for line in copyright_header_lines])
                    f.write('\n')
                    f.write(content)
