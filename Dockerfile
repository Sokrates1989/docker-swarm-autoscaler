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


# Make port 8790 available to the world outside this container.
EXPOSE 8790

# Copy the app.
COPY . /code

# Start api.
CMD ["python", "/code/src/scale_services.py"]
