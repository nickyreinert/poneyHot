#!/bin/bash

# Start Nginx
service nginx start

# Start Gunicorn
.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 httpServer:app
