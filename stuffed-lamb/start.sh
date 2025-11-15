#!/bin/bash
# Quick launcher - redirects to the full startup script
cd "$(dirname "$0")"
exec ./scripts/start-complete.sh
