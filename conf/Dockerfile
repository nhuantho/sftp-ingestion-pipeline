FROM apache/airflow:3.1.3-python3.12

ARG AIRFLOW_VERSION
ARG PYTHON_VERSION
ARG AIRFLOW_UID

USER 0
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         gcc \
         heimdal-dev

USER ${AIRFLOW_UID}
RUN python -m pip install --upgrade pip
COPY ./dependencies /tmp/
COPY ../dags /opt/airflow/dags/dags
COPY ../modules /opt/airflow/dags/modules

# Download the constraints file
RUN curl -o /tmp/constraints.txt https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt

# use constraints to reduce backtracking time
RUN pip install --no-cache-dir -r /tmp/internal-requirements.txt -c /tmp/constraints.txt \
    && pip install --no-cache-dir -r /tmp/external-requirements.txt \
