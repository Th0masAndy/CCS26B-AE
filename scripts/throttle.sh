#!/usr/bin/env bash

set -euo pipefail

MODE=${1:-}
DEV=${2:-lo}

if [[ $MODE != lan && $MODE != wan && $MODE != del ]]; then
    echo "usage: $0 {lan|wan|del} [network-interface]" >&2
    echo "warning: this command modifies the host qdisc and requires sudo" >&2
    exit 2
fi

if ! command -v tc >/dev/null 2>&1; then
    echo "error: tc was not found; install iproute2" >&2
    exit 2
fi

delete_qdisc()
{
    sudo tc qdisc del dev "$DEV" root 2>/dev/null || true
}

if [[ $MODE == del ]]; then
    delete_qdisc
    echo "🌐 Removed qdisc from $DEV"
    exit 0
fi

delete_qdisc
if [[ $MODE == lan ]]; then
    # Approximately 10 Gbit/s and 0.02 ms round-trip latency.
    sudo tc qdisc add dev "$DEV" root handle 1: tbf \
        rate 10000mbit burst 100000 limit 10000
    sudo tc qdisc add dev "$DEV" parent 1:1 handle 10: netem delay 0.01msec
else
    # Approximately 100 Mbit/s and 80 ms round-trip latency.
    sudo tc qdisc add dev "$DEV" root handle 1: tbf \
        rate 100mbit burst 100000 limit 10000
    sudo tc qdisc add dev "$DEV" parent 1:1 handle 10: netem delay 40msec
fi

echo "🌐 Configured $MODE profile on $DEV"
echo "   Cleanup: $0 del $DEV"
