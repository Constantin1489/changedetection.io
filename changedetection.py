#!/usr/bin/python3

# Only exists for direct CLI usage

import eventlet.hubs
eventlet.hubs.use_hub("eventlet.hubs.asyncio")
import changedetectionio
changedetectionio.main()
