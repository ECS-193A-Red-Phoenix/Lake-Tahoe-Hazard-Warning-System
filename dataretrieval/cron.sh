#!/bin/bash
cd "$(dirname "$0")";

now=$(date +"%T")
echo "Starting cron job at $now"

python3 service.py

now=$(date +"%T")
echo "Completed DataRetrieval cron job at $now"
