FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y netcat-openbsd jq && rm -rf /var/lib/apt/lists/*

COPY . .

# Make sure config.json exists (can be copied from config_example.json if needed)
RUN if [ ! -f config.json ]; then cp config_example.json config.json || echo "Please create a config.json file"; fi

# Create wait-for-mysql.sh script
# COPY wait-for-mysql.sh /wait-for-mysql.sh
# RUN chmod +x /wait-for-mysql.sh

# Create a file to indicate we're running in Docker
RUN touch /.dockerenv

EXPOSE 5001

CMD ["python", "app.py"]
