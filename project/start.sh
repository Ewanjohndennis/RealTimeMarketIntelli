#!/bin/bash

# start MCP tools server
python tools_server.py &

# start streamlit app
streamlit run app.py