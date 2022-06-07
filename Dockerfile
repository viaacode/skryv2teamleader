FROM python:3.7.6-alpine3.11

# Applications should run on port 8080 so NGINX can auto discover them.
EXPOSE 8080

RUN apk add --no-cache gcc musl-dev tzdata
RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime

# Copy all files
WORKDIR /src/usr/app
COPY . .


# Install packages
RUN pip3 install -r requirements.txt \
    --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
    --trusted-host do-prd-mvn-01.do.viaa.be && \
    pip3 install -r requirements-test.txt \
    --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
    --trusted-host do-prd-mvn-01.do.viaa.be && \
    pip3 install pycodestyle

# Run the application
ENTRYPOINT ["python3"]

# fast-api running on port 8080
CMD ["-m", "main"]

