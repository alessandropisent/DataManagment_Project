#!/bin/bash

# Number of parallel jobs (adjust based on CPU cores)
JOBS=4

# Function to compress a single file
compress_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        gzip -k "$file" && echo "Compressed: $file"
    fi
}

export -f compress_file

# Find and compress .tsv files in parallel
find . -maxdepth 1 -type f -name "*.tsv" | xargs -P "$JOBS" -I {} bash -c 'compress_file "$@"' _ {}

echo "Compression completed."
