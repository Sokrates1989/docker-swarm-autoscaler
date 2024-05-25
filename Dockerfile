# PYTHON.
FROM python:3.9

# Enable Virtual Environment.
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip, install and upgrade pip dependencies.
COPY install/pip_install.txt install/pip_upgrade.txt /code/
WORKDIR /code
RUN python3 -m venv $VIRTUAL_ENV \
    && python -m pip install --upgrade pip \
    && pip install --upgrade pip \
    && pip install -r pip_install.txt \
    && pip install -r pip_upgrade.txt --upgrade \
    && rm -rf /root/.cache/pip

### Environment variables ###

## Logging ##
# Available log levels: "INFO" | "VERBOSE" | "IMPORTANT_ONLY" .
ENV LOG_LEVEL="INFO"
# Available log styles: "PRINT_ONLY" | "LOGFILE_ONLY" | "PRINT_AND_LOGFILE" .
ENV LOG_STYLE="PRINT_AND_LOGFILE"
# TIMEZONE for location aware timestamps: https://mljar.com/blog/list-pytz-timezones/
ENV TIMEZONE=""

## Messaging ##

# Email.
ENV EMAIL_ENABLED="false"
# Sender.
ENV EMAIL_SENDER_USER="some.mail@domain.com"
ENV EMAIL_SENDER_PASSWORD_FILE=""
ENV EMAIL_SENDER_PASSWORD=""
ENV EMAIL_SENDER_HOST="smtp.example.com"
ENV EMAIL_SENDER_PORT="587"
# Recipients.
ENV EMAIL_RECIPIENTS_IMPORTANT=""
ENV EMAIL_RECIPIENTS_INFORMATION=""
ENV EMAIL_RECIPIENTS_VERBOSE=""

# Telegram.
ENV TELEGRAM_ENABLED="false"
# Sender Telegram bot token.
ENV TELEGRAM_SENDER_BOT_TOKEN_FILE=""
ENV TELEGRAM_SENDER_BOT_TOKEN=""
# Recipients.
ENV TELEGRAM_RECIPIENTS_IMPORTANT=""
ENV TELEGRAM_RECIPIENTS_INFORMATION=""
ENV TELEGRAM_RECIPIENTS_VERBOSE=""


# Copy the app.
COPY . /code

# Start api.
CMD ["python", "/code/src/scale_services.py"]
