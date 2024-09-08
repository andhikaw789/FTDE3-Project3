FROM apache/airflow:2.10.0-python3.8

# Switch to root to install packages and set permissions
USER root
COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" \
    apache-airflow-providers-apache-spark \
    -r /requirements.txt

# Set the correct permissions
RUN mkdir -p /sources/logs /sources/dags /sources/plugins \
    && chown -R airflow:root /sources

# Switch back to airflow user
USER airflow