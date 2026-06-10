#!/bin/bash
# Helper: copy SQL to /tmp for SSH piping
cp "$(dirname "$0")/001_initial_schema.sql" /tmp/ags_migration.sql
echo "Copied to /tmp/ags_migration.sql"
ls -la /tmp/ags_migration.sql
