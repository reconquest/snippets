#!/bin/bash

SESSION=$(tmux display-message -p "#S")
PANE_CURRENT=$SESSION:0.0
PANE_COMMANDS=$SESSION:0.1
FILENAME=main.go
FILE=$(tests:get-tmp-dir)/$FILENAME

tests:put $FILENAME <<CODE
package main

func main() {
	arg1 := 1
	arg2 := 2

	foo(
		arg1,
		arg2,
	)

	err := bar(
		arg2,
		arg1,
	)
}
CODE

LOCK_FILE=$(tests:get-tmp-dir)/commands.lock
tests:ensure /bin/touch $LOCK_FILE

:wait-for-commands() {
    while true; do
        if [ -f $LOCK_FILE ]; then
            sleep 1s
            continue
        fi

        return
    done
}

tests:ensure tmux split-window "tmux select-pane -t $PANE_CURRENT; /bin/zsh"

tests:ensure tmux send-keys -t $PANE_COMMANDS \
    vim Space $FILE Enter Enter \
    :w Enter \
    5jo x Tab Escape 8jo x Tab Escape \
    :w Enter \
    :\!rm Space $LOCK_FILE Enter

:wait-for-commands

tests:ensure tmux kill-pane -t $PANE_COMMANDS

EXPECTED_FILE_CONTENTS="
package main

func main() {
	arg1 := 1
	arg2 := 2

	log.Debugf(\"main.go:11: %s\", \"foo()\")
	log.Debugf(\"\t%s: %#v\", \"arg1\", arg1)
	log.Debugf(\"\t%s: %#v\", \"arg2\", arg2)

	foo(
		arg1,
		arg2,
	)

	log.Debugf(\"main.go:20: %s\", \"bar()\")
	log.Debugf(\"\t%s: %#v\", \"arg2\", arg2)
	log.Debugf(\"\t%s: %#v\", \"arg1\", arg1)

	err := bar(
		arg2,
		arg1,
	)
}
"

tests:assert-no-diff-blank "$EXPECTED_FILE_CONTENTS" "$(cat $FILE)"
