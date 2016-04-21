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
