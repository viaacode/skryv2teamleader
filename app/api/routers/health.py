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

router = APIRouter()


@router.get("/live")
async def liveness_check():
    """
    Returns OK if the service is running.
    """
    return "OK"
