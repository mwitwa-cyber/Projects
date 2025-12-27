# Use a slim Python base
FROM python:3.11-slim

# Install uv for fast package management
RUN pip install uv

WORKDIR /app

# Install dependencies strictly, including Jupyter
RUN uv pip install --system mcp pandas jupyterlab

# Copy the server logic
COPY server.py .

# Create the mount point for persistence
RUN mkdir /data

# Expose Jupyter port
EXPOSE 8888

# Launch Jupyter Lab
# We use --allow-root because we are running as root in this slim container
# We disable auth (tokens/passwords) for easy local access as requested
ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]
