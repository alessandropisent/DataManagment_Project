#!/bin/bash

# Number of parallel jobs (adjust based on CPU cores)
JOBS=4

# Function to decompress a single file
decompress_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        gunzip -k "$file" && echo "Decompressed: $file"
    fi
}

export -f decompress_file

# Find and decompress .tsv.gz files in parallel
find . -maxdepth 1 -type f -name "*.tsv.gz" | xargs -P "$JOBS" -I {} bash -c 'decompress_file "$@"' _ {}

echo "Decompression completed."
