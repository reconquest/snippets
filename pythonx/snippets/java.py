import vim

def guess_package_from_file_name():
    path = vim.eval('expand("%:p:h")')
    src = path.find('/src/')
    if src != -1:
        path = path[src+len('/src/'):]
        java = path.find('/java/')
        if java != -1:
            path = path[java+len('/java/'):]
    else:
        path = vim.eval('%:h')

    return path.replace('/', '.')
