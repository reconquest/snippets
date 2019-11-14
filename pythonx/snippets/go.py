import px
import px.autocommands
import px.buffer
import px.common
import px.completion
import px.cursor
import px.cursor.callbacks
import px.doc
import px.highlight
import px.identifiers
import px.langs
import px.langs.go
import px.langs.go.autoimport
import px.langs.go.completion
import px.langs.go.completion.unused
import px.langs.go.packages
import px.langs.go.test_completion
import px.langs.go.transform
import px.langs.go.transform.structs
import px.langs.java
import px.langs.php
import px.langs.python
import px.snippets
import px.syntax
import px.test
import px.util
import px.whitespaces
import re
import vim

def _line(snip, diff=0):
    return snip.buffer[snip.line + diff]


def should_expand_fallthrough(buffer, line):
    if not px.langs.go.is_case(buffer, line):
        return False

    return True


def should_expand_case(buffer, line):
    if not px.langs.go.is_switch(buffer, line):
        if not px.langs.go.is_select(buffer, line):
            return False

    return True



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


def is_comment():
    return px.syntax.is_comment(px.cursor.get())


def guess_package_from_file_name():
    return px.langs.go.packages.guess_package_name_from_file_name()


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


def get_value_for_if(current_value, context, value_tabstop=1):
    if 'tabstop' in context and context['tabstop'] != value_tabstop:
        return current_value

    value = px.snippets.complete_identifier_for_placeholder(
        px.cursor.get(),
        current_value,
        px.langs.go.get_not_used_identifier_completion
    )

    if value == 'err':
        value = 'err != nil'

    return value


def jump_to_if_body_on_err_not_nil(snip):
    snip.context['tabstop'] = snip.tabstop
    if len(snip.tabstops) <= 1:
        return

    if snip.tabstops[1].current_text == "err != nil":
        if snip.tabstop == 1:
            if snip.jump_direction == 1:
                vim.command('call feedkeys("\<C-J>")')

        if snip.tabstop == 2:
            px.snippets.expect_cursor_jump(
                px.cursor.get(),
                px.snippets._highlight_completion
            )


def action_define_method(cursor, context, tabstops, pointer=False):
    a_left = '('
    a_right = ')'

    buffer = px.buffer.get()

    line = context['line'] - 1

    contents = buffer[line]
    if line-1 < len(buffer) and len(buffer[line-1]) > 0:
        if buffer[line-1][0] == "\t":
            if buffer[line-1][-1] != '{':
                x = 0
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
    r_right = ''
    if tabstops[3]:
        r_right = ' '

    if "," in tabstops[3]:
        r_left = ' ('
        r_right = ') '

    prev_binding = px.langs.go.extract_prev_method_binding(
        buffer, cursor
    )

    if not prev_binding:
        return

    name, type = prev_binding

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
        if not prev_line.strip().endswith('{'):
            return True

    return False


def is_inside_docopt_section(snip, section):
    if not px.syntax.is_string(px.cursor.from_vim(snip.cursor)):
        return False

    match = px.whitespaces.match_higher_indent(snip.buffer, snip.cursor,
        '(?i)' + section)
    if not match:
        return False

    return True


def docopt_format_options(snip, separator='  ', indenting=' '):
    match = px.whitespaces.match_higher_indent(snip.buffer, snip.cursor,
        '(?i)options')
    if not match:
        return

    options_line, options_line_number = match

    while True:
        match = px.whitespaces.match_exact_indent_as_in_line(
            snip.buffer,
            (options_line_number - 1, 0),
            options_line,
            '(?i)options',
            direction=-1,
        )

        if not match:
            break

        options_line_number, _ = match

    usage_begins_at = options_line_number + 1

    longest_option, usage_ends_at = docopt_get_longest_option(snip.buffer,
        usage_begins_at)

    docopt_align_options(snip.buffer, snip.cursor, len(longest_option),
        usage_begins_at,
        usage_ends_at,
        separator, indenting)

    snip.cursor.set(snip.cursor[0], len(snip.buffer[snip.cursor[0]]))


def docopt_get_longest_option(buffer, usage_begins_at):
    tab_width = int(int(vim.eval('&ts')) / 2)

    usage_ends_at = usage_begins_at
    longest_option = ''
    for line in buffer[usage_begins_at:]:
        if line.strip() == '`' or line.strip() == '`)':
            break

        option = parse_docopt_option(line, tab_width)
        if option:
            if len(option['first_column']) > len(longest_option):
                longest_option = option['first_column']

        usage_ends_at += 1

    return longest_option, usage_ends_at


def docopt_align_options(
    buffer, cursor, longest_option_length,
    usage_begins_at, usage_ends_at,
    separator, indenting
):
    tab_width = int(vim.eval('&ts'))

    for (index, line) in enumerate(buffer[usage_begins_at:usage_ends_at]):
        if index + usage_begins_at == cursor[0]:
            continue

        option = parse_docopt_option(line, tab_width)
        if not option:
            continue

        indent = ''

        if option['first_column'].strip() == '':
            indent = indenting

        buffer[usage_begins_at+index] = \
            option['first_column'].ljust(longest_option_length) + \
            separator + \
            indent + option['second_column']


def parse_docopt_option(line, tab_width=4):
    match = re.match(
        """(?x)
            ^(?P<indent>(?P<first>
                (\s+)
                (
                    (
                        (
                            \s*?
                            (-[\w-]* ([ =]( <[\w_-]+>|[A-Z_]+) )? )
                        ) | (
                            ( <[\w_-]+> | ([A-Z_]+(?!\s\S|\S)) | \S+\s{2,} )
                        )
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
        int(int(vim.eval('&ts')) / 2)
    )

    if len(opt_line) > 79 and ' ' in t[2]:
        split_boundary = len(opt_line) - len(t[2])
        first_line, second_line = t[2].rsplit(' ', 1)

        indentation = ' ' * (split_boundary + 1)  # +1 for extra indenting

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


def generate_implementation(snip):
    prev_binding = px.langs.go.extract_prev_method_binding(
        snip.buffer, snip.cursor
    )

    if not prev_binding:
        return

    name, type = prev_binding

    interface = snip.buffer[snip.cursor[0]]

    del snip.buffer[snip.cursor[0]]

    vim.command('call feedkeys("\<ESC>:GoImpl {} {} {}\<CR>")'.format(
        name,
        "*"+type,
        interface,
    ))

    snip.cursor.preserve()


def extract_comment_subject(
    snip,
    kind=['type', 'func', 'var', 'const']
):
    if is_string():
        return

    if snip.line > 0:
        prev_line = snip.buffer[snip.line - 1]
        if prev_line.strip().startswith('//'):
            return

    next_line = snip.buffer[snip.line + 1]

    matches = re.match(r'^type (\w+)', next_line)
    if matches and 'type' in kind:
        return matches.group(1)

    matches = re.match(r'^func (\([^\)]+\)\s)?(\w+)', next_line)
    if matches and 'func' in kind:
        return matches.group(2)

    matches = re.match(r'^(var|const) ([\w]+)', next_line)
    if matches and ('const' in kind or 'var' in kind):
        return matches.group(2)
