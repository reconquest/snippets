import vim
import os
import os.path
import px
import px.buffer

def guess_package_name_from_file_name():
    path = os.path.dirname(px.buffer.get().name)
    src = path.find('/src/')
    if src != -1:
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
