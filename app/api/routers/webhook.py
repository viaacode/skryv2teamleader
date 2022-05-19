#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/api/routers/webhook.py
#
#   list, create and remove webhooks for skryv
#   we use a background worker
#

from fastapi import APIRouter, BackgroundTasks
from app.app import main_app as app
# from typing import Optional

router = APIRouter()


class Worker:
    def __init__(self):
        self.create_running = False
        self.delete_running = False
        self.update_running = False

    def create_webhooks_job(self):
        self.create_running = True
        app.create_webhooks()
        self.create_running = False

    def update_webhooks_job(self):
        self.update_running = True
        app.update_webhooks()
        self.update_running = False

    def delete_webhooks_job(self):
        self.delete_running = True
        app.delete_webhooks()
        self.delete_running = False


worker = Worker()


@router.get("/list")
def list_webhooks():
    return app.list_webhooks()


@router.post("/create")
async def create_webhooks(background_tasks: BackgroundTasks):
    if not worker.create_running:
        status = 'create webhooks started.'
        background_tasks.add_task(worker.create_webhooks_job)
    else:
        status = 'create webhooks already running.'

    return {'status': status}


@router.post("/update")
async def update_webhooks(background_tasks: BackgroundTasks):
    if not worker.update_running:
        status = 'update webhooks started.'
        background_tasks.add_task(worker.update_webhooks_job)
    else:
        status = 'update webhooks already running.'

    return {'status': status}


@router.delete("/remove")
async def delete_webhooks(background_tasks: BackgroundTasks):
    if not worker.delete_running:
        status = 'delete webhooks started.'
        background_tasks.add_task(worker.delete_webhooks_job)
    else:
        status = 'delete webhooks already running.'

    return {'status': status}
