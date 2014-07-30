FROM jaredkerim/mysql-community 

ADD . /src 
RUN mkdir -p /pip/cache
RUN pip install --download-cache /pip/cache --no-deps -r /src/requirements/dev.txt

EXPOSE 2602

CMD ["python", "src/manage.py", "runserver"]
