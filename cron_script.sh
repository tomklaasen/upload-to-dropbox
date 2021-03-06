#!/bin/bash

PIDFILE=/home/pi/upload-to-dropbox.pid


if [ -f $PIDFILE ]
then
  PID=$(cat $PIDFILE)
  ps -p $PID > /dev/null 2>&1
  if [ $? -eq 0 ]
  then
    # echo "Process already running"
    exit 1
  else
    ## Process not found assume not running
    echo $$ > $PIDFILE
    if [ $? -ne 0 ]
    then
      # echo "Could not create PID file"
      exit 1
    fi
  fi
else
  echo $$ > $PIDFILE
  if [ $? -ne 0 ]
  then
    # echo "Could not create PID file"
    exit 1
  fi
fi

cd /home/pi/upload-to-dropbox/
python /home/pi/upload-to-dropbox/main.py

rm $PIDFILE
