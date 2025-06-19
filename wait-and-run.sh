#!/bin/sh
set -e
delay="$1"
shift
cmd="$@"
echo "Waiting for $delay seconds before starting..."
sleep "$delay"
echo "Executing command: $cmd"
exec $cmd