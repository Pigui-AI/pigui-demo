# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY streamlit_chat_branch.py .

# Expose port 8080
EXPOSE 8080

# Run Streamlit on port 8080
CMD ["streamlit", "run", "streamlit_chat_branch.py", "--server.port=8080", "--server.address=0.0.0.0"]
