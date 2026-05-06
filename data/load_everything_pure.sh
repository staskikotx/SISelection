#!/bin/bash

# Configuration - adjust if your path differs from the example
BASE_DIR="/home/ashulgin/material/alpha-sql/bird"
DEV_DATABASES_DIR="${BASE_DIR}/dev_databases"

# Verify critical paths exist
if [[ ! -d "$DEV_DATABASES_DIR" ]]; then
    echo "ERROR: Database directory not found at $DEV_DATABASES_DIR" >&2
    echo "Please update BASE_DIR in the script to match your environment" >&2
    exit 1
fi

# Check for pgloader
if ! command -v pgloader &> /dev/null; then
    echo "ERROR: pgloader is not installed or not in PATH" >&2
    echo "Install with: sudo apt-get install pgloader" >&2
    exit 1
fi

echo "Starting database upload process..."
echo "Scanning: $DEV_DATABASES_DIR"

# Process each database directory
for db_dir in "$DEV_DATABASES_DIR"/*; do
    # Skip non-directories
    [[ -d "$db_dir" ]] || continue
    
    db_name=$(basename "$db_dir")
    sqlite_path="${db_dir}/${db_name}.sqlite"
    pg_db_name="pure_${db_name}"
    
    # Verify SQLite file exists
    if [[ ! -f "$sqlite_path" ]]; then
        echo "⚠️  Skipping '${db_name}': SQLite file missing at ${sqlite_path}" >&2
        continue
    fi

    echo -e "\n--- Loading ${db_name} ---"
    echo "Source: ${sqlite_path}"
    echo "Target: ${pg_db_name}"
    
    dropdb --if-exists --force $pg_db_name 
    createdb -T template0 "$pg_db_name" 2>/dev/null || true
    
    # Execute pgloader with error handling
    if pgloader "$sqlite_path" "postgresql:///$pg_db_name"; then
        echo "✅ Successfully loaded ${pg_db_name}"
    else
        echo "❌ FAILED to load ${pg_db_name}" >&2
        # Optional: uncomment to stop on first error
        # exit 1
    fi

done

echo -e "\nProcess complete! Summary:"
echo "• Total databases found: $(find "$DEV_DATABASES_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)"
echo "• Successfully loaded: $(psql -lqtA | grep '^pure_' | wc -l)"
echo "• Failed loads: Check error messages above"