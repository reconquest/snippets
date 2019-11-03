def get_selected_placeholder(snip):
    return snip.last_placeholder and snip.last_placeholder.current_text

def is_first_line(snip):
    return snip.line == 0
