FROM postgres:15-alpine
RUN pip install --upgrade setuptools==78.1.1
COPY src_postgres/init.sql /docker-entrypoint-initdb.d/