#!/bin/bash

host=$1
course=$2
role=$3
key=$4
shift 4

usernames=$(printf '"%s",' "$@")
usernames="[${usernames%,}]"

curl -v -X POST \
  "$host"'/api/courses/'"$course"'/'"$role" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $key" \
  --data "$usernames"

