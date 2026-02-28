BOT_NAME = "ministryOfFinance"

SPIDER_MODULES = ["ministryOfFinance.spiders"]
NEWSPIDER_MODULE = "ministryOfFinance.spiders"

from fake_useragent import UserAgent
USER_AGENT = UserAgent().random
ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 0.5
RANDOMIZE_DOWNLOAD_DELAY = 0.2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

ITEM_PIPELINES = {
    'ministryOfFinance.pipelines.CustomFileStoragePipeline': 300,
}

import crawlab
FILES_STORE = crawlab.get_task_export_dir()
LOG_LEVEL = 'INFO'
CUTOFF_DATE = '2025-12-1'
INCREMENTAL_MODE = True
