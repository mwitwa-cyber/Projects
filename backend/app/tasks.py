"""
Celery Beat Scheduler for Data Pipelines
"""
from celery import Celery
from celery.schedules import crontab
import logging

from backend.services.data_pipelines.luse_scraper import fetch_luse_prices
from backend.services.data_pipelines.boz_yield_curve import fetch_boz_yield_curve
from backend.services.data_pipelines.zamstats import fetch_zamstats_cpi

logger = logging.getLogger("scheduler")

celery_app = Celery('tasks')
celery_app.conf.broker_url = 'redis://redis:6379/0'
celery_app.conf.result_backend = 'redis://redis:6379/0'

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Daily LUSE update (weekdays at 5:30 PM)
    sender.add_periodic_task(
        crontab(hour=17, minute=30, day_of_week='1-5'),
        daily_luse_update.s(),
        name='Fetch LUSE prices daily'
    )
    # Weekly BoZ yield curve update (Monday 9 AM)
    sender.add_periodic_task(
        crontab(hour=9, minute=0, day_of_week='1'),
        weekly_boz_yield_curve_update.s(),
        name='Fetch BoZ yield curve weekly'
    )
    # Monthly ZamStats CPI update (1st of month at 10 AM)
    sender.add_periodic_task(
        crontab(hour=10, minute=0, day_of_month='1'),
        monthly_zamstats_cpi_update.s(),
        name='Fetch ZamStats CPI monthly'
    )

@celery_app.task
def daily_luse_update():
    logger.info("Running daily LUSE update...")
    fetch_luse_prices()

@celery_app.task
def weekly_boz_yield_curve_update():
    logger.info("Running weekly BoZ yield curve update...")
    fetch_boz_yield_curve()

@celery_app.task
def monthly_zamstats_cpi_update():
    logger.info("Running monthly ZamStats CPI update...")
    fetch_zamstats_cpi()
