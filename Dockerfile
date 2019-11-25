FROM postgres:latest

USER postgres
COPY ./init-user-db.sh /docker-entrypoint-initdb.d
EXPOSE 5432
RUN /etc/init.d/postgresql start
