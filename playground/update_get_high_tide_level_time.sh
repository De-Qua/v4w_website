#!/bin/bash
echo "launching the python script for reading tide level.."
python3 get_high_tide_level.py
echo "and updating time.."
pa_update_scheduled_task.py $1 -m $(date -d"$(date) + 5 minute" +"%M") -p
echo "updated scheduled task"
