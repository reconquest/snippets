import re
import os.path
import vim

import px.go
import px.all

def _buffer():
    return vim.current.buffer

def _cursor():
    return vim.current.window.cursor

def _line(snip, diff=0):
    return snip.buffer[snip.line + diff]

def should_expand_case(buffer, line):
    if not px.go.is_switch(buffer, line):
        return False

    switch_line = px.go.get_bracket_line(buffer, line)
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


def is_if_body(buffer, line):
	return re.match('^\s+if.*err ', px.util.get_prev_nonempty_line(buffer, line))


def is_string():
	return px.all.is_syntax_string(_cursor())


def get_value_for_if():
	value = px.all.get_last_defined_var_for_snippet()
	if value == 'err':
		value = 'err != nil'

	return value


def jumper_if(snip):
	if snip.tabstops[1].current_text == "err != nil" and snip.tabstop == 1 and snip.jump_direction == 1 :
		vim.command('call feedkeys("\<C-J>")')


def action_define_method(snip, t, pointer=False):
	a_left = '('
	a_right = ')'

	buffer = _buffer()
	line = snip.context['snip'].line + 1

	contents = buffer[line]
	if line+1 < len(buffer) and buffer[line+1][0] == "\t" and buffer[line][-1] != '{':
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

	if "," in t[3]:
		r_left = ' ('
		r_right = ') '

	name, type = px.go.extract_prev_method_binding_for_cursor()
	if pointer:
		type = '*' + type

	binding = name + ' ' + type

	return (a_left, a_right, r_left, r_right, binding)


def gocode_complete_function(snip):
	(snip_ret, snip_func) = px.go.get_gocode_complete(False)
	snip_full = px.go.get_gocode_complete(True)

	cur_line = re.sub('\w+\.\w+$', '', _line(snip)[:snip.column])
	cur_line = cur_line + "" + _line(snip)[snip.column+1:]
	snip.buffer[snip.line] = cur_line

	prev_line = px.util.get_prev_nonempty_line(snip.buffer, snip.line)

	if prev_line[-1] == ',' or prev_line[-1] == '(' or prev_line[-1] == '&' or cur_line.strip() != '':
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
		'post_jump': """placeholder_err = """+placeholder_err +"""
if snip.tabstop == 0:
	err = snip.tabstops[placeholder_err].current_text
	if err != '_':
		snip.expand_anon("\\nif " + err + " != nil {\\n\\t$1\\n}")
"""
	}

	snip.expand_anon(
		snip_full,
		actions = actions,
	)


def should_expand_amp(buffer, line, column):
	line_contents = buffer[line]

	if line_contents.strip().startswith('if '):
		return True

	prev_line = px.util.get_prev_nonempty_line(buffer, line)

	higher = px.util.get_higher_indent(buffer, (line, 0))
	if not higher:
		return False

	(higher_line, _) = higher

	if prev_line == higher_line and prev_line.strip().startswith('if '):
		return True

	return False
