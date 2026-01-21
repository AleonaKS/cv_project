BOT_NAME = 'book_covers_spider'

SPIDER_MODULES = ['backend.spiders']
NEWSPIDER_MODULE = 'backend.spiders'

ROBOTSTXT_OBEY = True

# Настройки для вежливого парсинга
CONCURRENT_REQUESTS = 2
DOWNLOAD_DELAY = 2.0
RANDOMIZE_DOWNLOAD_DELAY = True

# Настройки кэширования (опционально)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600

# User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Логирование
LOG_LEVEL = 'INFO'
