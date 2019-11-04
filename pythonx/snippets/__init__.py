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

def get_selected_placeholder(snip):
    return snip.last_placeholder and snip.last_placeholder.current_text

def is_first_line(snip):
    return snip.line == 0
