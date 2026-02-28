BOT_NAME = "ministryOfEducation"

SPIDER_MODULES = ["ministryOfEducation.spiders"]
NEWSPIDER_MODULE = "ministryOfEducation.spiders"

from fake_useragent import UserAgent
USER_AGENT = UserAgent().random
ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 0.5
RANDOMIZE_DOWNLOAD_DELAY = 0.2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

ITEM_PIPELINES = {
    'ministryOfEducation.pipelines.CustomFileStoragePipeline': 300,
}

import crawlab
FILES_STORE = crawlab.get_task_export_dir()
LOG_LEVEL = 'INFO'
CUTOFF_DATE = '2025-12-1'
INCREMENTAL_MODE = True