#!/usr/bin/env bash
# macOS + Homebrew: fix SAM CLI pyexpat ImportError (Python 3.14 / libexpat mismatch)
if [[ "$(uname -s)" == "Darwin" ]] && [[ -d /opt/homebrew/opt/expat/lib ]]; then
  export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi
