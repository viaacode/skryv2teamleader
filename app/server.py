#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/server.py
#
#   Webserver implementation using FastAPI to expose a json api to various tasks
#   for synchronizing companies and contacts between Teamleader and LDAP.
#   look at app/api/api.py for actual routes defined and also app/routers dir.
#

from fastapi import FastAPI
from fastapi.responses import RedirectResponse  # , HTMLResponse
from fastapi_route_logger_middleware import RouteLoggerMiddleware
from viaa.configuration import ConfigParser
from viaa.observability import logging
from app.api.api import api_router
from app.app import main_app


app = FastAPI(
    title="Skryv2Teamleader",
    description="Receive skryv webhooks and make updates in teamleader.",
    version="1.0.0",
)

app.include_router(api_router)
config = ConfigParser()
log = logging.get_logger(__name__, config=config)

# we disable logging of health calls
app.add_middleware(
    RouteLoggerMiddleware,
    logger=log,
    skip_routes=['/health']
)


@app.on_event("startup")
def startup_event():
    redis_url = config.app_cfg['teamleader']['redis_url']
    main_app.redis_cache.create_connection(redis_url)
    main_app.start_clients()
    main_app.clients.slack.server_started_message()


@app.on_event('shutdown')
async def shutdown_event():
    if config.app_cfg['teamleader']['redis_url'] != 'DISABLED':
        main_app.redis_cache.close()


@app.get("/", include_in_schema=False)
def read_root():
    """ make root path show the API swagger docs """
    return RedirectResponse("/docs")
