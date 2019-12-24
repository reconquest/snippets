import vim
import os
import os.path
import px
import px.buffer
import re

DEFAULT_TYPE_TOKEN = "class"

def guess_type_from_dir():
    path = os.path.dirname(px.buffer.get().name)

    # key = (class|interface)
    # value = number of mentions
    result = {}
    for dirpath, dnames, fnames in os.walk(path):
        for name in fnames:
            fullname = os.path.join(dirpath, name)
            token = get_type_from_file(fullname)
            if token in result:
                result[token] += 1
            else:
                result[token] = 0

    max_token = DEFAULT_TYPE_TOKEN
    max_mentions = 0
    for item in result.items():
        token, mentions = item
        if mentions > max_mentions:
            max_token = token

    return max_token


def get_type_from_file(path):
    with open(path) as file:
        for line in file:
            matches = re.match(
                r'(public|private)\s*(static)?\s*(class|interface)',
                line
            )

            if not matches:
                continue

            token = matches.group(3)
            return token
    return DEFAULT_TYPE_TOKEN


def guess_package_name_from_file_name():
    path = os.path.dirname(px.buffer.get().name)

    found = True
    src = path.find('src/')
    if src == -1 and not path.startswith('src/'):
        found = False

    if found:
        path = path[src+len('/src/'):]
        java = path.find('/java/')
        if java != -1:
            path = path[java+len('/java/'):]
    else:
        path = os.path.basename(path)

    return path.replace('/', '.')

def guess_class_name_from_file_name():
    return os.path.basename(px.buffer.get().name).replace('.java', '')

def guess_imports_from_file_name():
    class_name = guess_class_name_from_file_name()

    imports = []
    if class_name.endswith('Response') or class_name.endswith('Request'):
        imports.append("javax.xml.bind.annotation.*")

    contents = ""
    if len(imports) > 0:
        contents = "\n".join(map(lambda x: "import "+x+";", imports))
        contents = "\n" + contents + "\n"
        return contents
    return ""
