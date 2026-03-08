#!/bin/bash
cd "$(dirname "$0")/.."
python -m season1.balance_harness "$@"
