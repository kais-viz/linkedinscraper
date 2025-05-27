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

# Update host to 'db' in config.json when running in Docker
RUN if [ -f config.json ]; then \
  DB_TYPE=$(jq -r '.db_type // ""' config.json); \
  if [ "$DB_TYPE" = "mysql" ]; then \
  TMP=$(mktemp) && \
  jq '.host = "db"' config.json > "$TMP" && \
  mv "$TMP" config.json; \
  fi; \
  fi

EXPOSE 5001

CMD ["python", "app.py"]
