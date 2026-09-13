#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

ns=(12)
dims=(2 4 6)
deltas=(32 64 128 256 512)
metrics=(0 1 2)
TRIALS=${TRIALS:-1}
VERIFY=${VERIFY:-1}

if [[ ! $TRIALS =~ ^[1-9][0-9]*$ ]] || (( ${#TRIALS} > 10 )) || (( TRIALS > 2147483647 )); then
    echo "error: TRIALS must be an integer between 1 and 2147483647" >&2
    exit 2
fi

run_fpsi()
{
  ./code/build/fpsi "$@" -inter 4 -try "$TRIALS" -v "$VERIFY"
}

printf "[ProType]  [Assumption]   [Metric] [Dim] [Delta] [Size] [Com.(MB)] [Time(s)]\n"

echo "▶ uniqueBlock / receiver / normal"
for metric in "${metrics[@]}"; do
  for nn in "${ns[@]}"; do
    for dim in "${dims[@]}"; do
      for delta in "${deltas[@]}"; do
        run_fpsi -assumption 1 -p "$metric" -nn "$nn" \
          -d "$dim" -delta "$delta"
      done
      echo
    done
  done
done

echo "▶ uniqueBlock / receiver / prefix"
for metric in "${metrics[@]}"; do
  for nn in "${ns[@]}"; do
    for dim in "${dims[@]}"; do
      for delta in "${deltas[@]}"; do
        run_fpsi -assumption 1 -prefix -p "$metric" -nn "$nn" \
          -d "$dim" -delta "$delta"
      done
      echo
    done
  done
done
