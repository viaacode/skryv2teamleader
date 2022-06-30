#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/api/routers/health.py
#
#   Router for openshift liveness check
#
from fastapi import APIRouter
from app.app import main_app as app

router = APIRouter()


@router.get("/live")
async def liveness_check():
    """
    Returns OK if the service is running.
    """
    return "OK"


@router.get("/oauth")
async def oauth_check():
    """
    Returns ok if oauth tokens are valid
    or link to refresh authentication if it's invalid
    """
    return app.oauth_check()
