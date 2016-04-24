import re
import vim

import px.util
import px.whitespaces
import px.buffer
import px.snippets
import px.cursor

import px.langs.go


def _line(snip, diff=0):
    return snip.buffer[snip.line + diff]


def should_expand_case(buffer, line):
    if not px.langs.go.is_switch(buffer, line):
        return False

    switch_line = px.langs.go.get_bracket_line(buffer, line)
    switch_line_indent = px.util.get_indentation(buffer[switch_line])

    if switch_line_indent == px.util.get_indentation(buffer[line]):
        return True

    return False


def is_first_line(snip):
    return snip.line == 0


def is_if_condition(snip):
    current_line = _line(snip)
    if re.search("^\s+if ", current_line):
        return True
    prev_line = _line(snip, -1)
    if re.search("&&\s+$", prev_line) or re.search("\|\|\s+$", prev_line):
        return True
    return False


def is_if_body(snip):
    return px.whitespaces.match_higher_indent(snip.buffer, snip.cursor, 'if ')


def is_for_body(snip):
    return px.whitespaces.match_higher_indent(snip.buffer, snip.cursor, 'for ')


def is_func_decl(snip):
    return px.langs.go.is_func_declaration(snip.buffer, snip.line)


def is_type_decl(snip):
    return px.langs.go.is_type_declaration(snip.buffer, snip.line)


def is_before_first_func(snip):
    return px.langs.go.is_before_first_func(snip.buffer, snip.line)


def is_string():
    return px.syntax.is_string(px.cursor.get())


def guess_package_from_file_name(path):
    return px.langs.go.packages.guess_package_name_from_file_name(path)


def get_value_for_for(current_value):
    def skip_err(identifier):
        if px.common.get_active_identifier_skipper()(identifier):
            return True

        if identifier.name == 'err':
            return True

        return False

    value = px.snippets.complete_identifier_for_placeholder(
        px.cursor.get(),
        current_value,
        px.langs.go.get_not_used_identifier_completion,
        should_skip=skip_err,
    )

    return value


def get_value_for_if(current_value):
    value = px.snippets.complete_identifier_for_placeholder(
        px.cursor.get(),
        current_value,
        px.langs.go.get_not_used_identifier_completion
    )

    if value == 'err':
        value = 'err != nil'

    return value


def jump_to_if_body_on_err_not_nil(snip):
    if snip.tabstops[1].current_text == "err != nil":
        if snip.tabstop == 1:
            if snip.jump_direction == 1:
                vim.command('call feedkeys("\<C-J>")')

        if snip.tabstop == 2:
            px.snippets.expect_cursor_jump(px.cursor.get())


def action_define_method(snip, tabstops, pointer=False):
    a_left = '('
    a_right = ')'

    buffer = px.buffer.get()
    buffer = px.cursor.get()

    line = snip.context['snip'].line + 1

    contents = buffer[line]
    if line+1 < len(buffer):
        if buffer[line+1][0] == "\t" and buffer[line][-1] != '{':
            x = 1
            while True:
                if line+x >= len(buffer):
                    break

                contents = contents + buffer[line+x].strip()

                if buffer[line+x] != '' and buffer[line+x][0] == ')':
                    break

                x += 1

    if len(contents) > 80:
        a_left = "(\n\t"
        a_right = "\n)"

    r_left = ' '
    r_right = ' '

    if "," in tabstops[3]:
        r_left = ' ('
        r_right = ') '

    name, type = px.langs.go.extract_prev_method_binding(
        snip.buffer, snip.cursor
    )
    if pointer:
        type = '*' + type

    binding = name + ' ' + type

    return (a_left, a_right, r_left, r_right, binding)


def gocode_complete_function(snip):
    (snip_ret, snip_func) = px.langs.go.get_gocode_complete(False)
    snip_full = px.langs.go.get_gocode_complete(True)

    curr_line = re.sub('\w+\.\w+$', '', snip.buffer[snip.line][:snip.column])
    column_before_expand = len(curr_line)
    curr_line = curr_line + "" + snip.buffer[snip.line][snip.column+1:]

    snip.buffer[snip.line] = curr_line

    prev_line = px.buffer.get_prev_nonempty_line(snip.buffer, snip.line)

    px.cursor.set((snip.line, column_before_expand))

    if prev_line[-1] in ',(&' or curr_line.strip() != '':
        snip.expand_anon(snip_func)
        return

    matches = re.search('\${(\d+):error}', snip_ret)
    if not matches:
        snip.expand_anon(snip_full)
        return

    placeholder_err = matches.group(1)
    snip_full = snip_full.replace(
        '${'+placeholder_err+':error}',
        '${'+placeholder_err+':err}',
    )

    actions = {
        'post_jump': """placeholder_err = """ + placeholder_err + """
if snip.tabstop == 0:
    err = snip.tabstops[placeholder_err].current_text
    if err != '_':
        snip.expand_anon("\\nif " + err + " != nil {\\n\\t$1\\n}")
"""
    }

    snip.expand_anon(
        snip_full,
        actions=actions,
    )


def should_expand_amp(snip):
    snip.line_contents = snip.buffer[snip.line]

    if snip.line_contents.strip().startswith('if '):
        return True

    prev_line = px.buffer.get_prev_nonempty_line(snip.buffer, snip.line)

    higher = px.whitespaces.get_higher_indent(snip.buffer, (snip.line, 0))
    if not higher:
        return False

    (higher_line, _) = higher

    if prev_line == higher_line and prev_line.strip().startswith('if '):
        return True

    return False


def is_inside_docopt_section(snip, section):
    if not px.syntax.is_string(px.cursor.from_vim(snip.cursor)):
        return False

    match = px.whitespaces.match_higher_indent(snip.buffer, snip.cursor, '(?i)' + section)
    if not match:
        return False

    return True

def docopt_format_options(snip, separator='  ', indenting=' '):
    match = px.whitespaces.match_higher_indent(snip.buffer, snip.cursor, '(?i)options')
    if not match:
        return

    usage_begins_at = match[1] + 1
    usage_ends_at = usage_begins_at
    longest_option = ''

    tab_width = int(vim.eval('&ts'))

    for line in snip.buffer[usage_begins_at:]:
        if line.strip() == '`':
            break

        if re.match(r'^\w', line.strip()):
            break

        option = parse_docopt_option(line, tab_width)

        if len(option['first_column']) > len(longest_option):
            longest_option = option['first_column']

        usage_ends_at += 1

    for (index, line) in enumerate(snip.buffer[usage_begins_at:usage_ends_at]):
        if index + usage_begins_at == snip.cursor[0]:
            continue

        option = parse_docopt_option(line, tab_width)
        indent = ''

        if option['first_column'].strip() == '':
            indent = indenting

        snip.buffer[usage_begins_at+index] = \
            option['first_column'].ljust(len(longest_option)) + \
            separator + \
            indent + option['second_column']


    snip.cursor.set(snip.cursor[0], len(snip.buffer[snip.cursor[0]]))

def parse_docopt_option(line, tab_width=4):
    print(line)
    match = re.match(
        """(?x)
            ^(?P<indent>(?P<first>
                (\s+)
                (
                    (
                        \s*?
                        (--?\w* ([= ]?(<[\w-]+>|[A-Z_]+))? )
                    )+
                )?
            )
            \s+)
            (?P<second>.*)
        """,
        line.expandtabs(tab_width)
    )

    if not match:
        return None

    result = {
        'first_column': match.group('first'),
        'second_column': match.group('second'),
        'indent': len(match.group('indent'))
    }

    if result['first_column'].strip() == '':
        result['first_column'] = ''

    return result

def split_long_docopt_line(t, snip):
    if snip.c != "":
        return snip.c

    opt_line = snip.buffer[snip.snippet_start[0]].expandtabs(
        int(vim.eval('&ts'))
    )

    if len(opt_line) > 79:
        split_boundary = len(opt_line) - len(t[2])
        first_line, second_line = t[2].rsplit(' ', 1)

        indentation = ' ' * (split_boundary + 1) # +1 for extra indenting

        t[2] = indentation + second_line

        return first_line + "\n"
    else:
        return ''

def get_options_indentation(snip):
    if snip.buffer.cursor[0] != snip.snippet_start[0]:
        return snip.c

    tab_width = int(vim.eval('&ts'))

    prev_opt = parse_docopt_option(
        snip.buffer[snip.snippet_start[0]-1], tab_width
    )

    if not prev_opt:
        return snip.c

    curr_opt = parse_docopt_option(
        snip.buffer[snip.snippet_start[0]], tab_width
    )

    if not curr_opt:
        return snip.c

    curr_indent = len(curr_opt['first_column'])

    if prev_opt['first_column'] == '':
        prev_indent = prev_opt['indent'] - 1
    else:
        prev_indent = prev_opt['indent']

    if curr_indent >= prev_indent:
        return ' ' * 2

    return ' ' * (prev_indent - curr_indent)
