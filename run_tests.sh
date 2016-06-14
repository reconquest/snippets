#!/bin/bash

set -euo pipefail

source ./vendor/github.com/reconquest/import.bash/import.bash

import "github.com/reconquest/test-runner"
import "github.com/reconquest/tests.sh"
import "github.com/reconquest/sudo"

:main() {
    tests:init
    test-runner:run "${@}"
}

:main "${@}"
