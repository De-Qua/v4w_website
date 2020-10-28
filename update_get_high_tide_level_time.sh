#!/bin/bash
pa_update_scheduled_task.py $1 -m $(date -d"$(date) + 5 minute" +"%M") -p
echo "ora lo lanciamo manualmente noi - ciao pythonanywhere"
python3 get_high_tide_level.py
echo "è successo qualcosa?"
