#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers (inspiration/tip for using fast-api: Rudolf Degeijter)
#
#   app/api/api.py
#
#   Import routers for webhooks skryv and teamleader auth calls
#   with oauth token support and managing webhook installation and list calls.
#   health for the healthchecks.
#

from fastapi import APIRouter
from app.api.routers import skryv, webhook, health

api_router = APIRouter()


api_router.include_router(
    skryv.router,
    prefix="/skryv",
    tags=["Skryv webhooks (save changes to Teamleader)"]
)

api_router.include_router(
    webhook.router,
    prefix="/webhooks",
    tags=["Manage Skryv Webhooks"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health check"]
)
