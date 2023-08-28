""" Startup file for Google Cloud deployment or local webserver"""
import os

from flathunter.argument_parser import parse
from flathunter.idmaintainer import IdMaintainer
from flathunter.googlecloud_idmaintainer import GoogleCloudIdMaintainer
from flathunter.web_hunter import WebHunter
from flathunter.config import Config
from flathunter.logging import configure_logging

from flathunter.web import app


import sentry_sdk


sentry_sdk.init(
    dsn="https://9071c86899b3e5d3c8c67e91868c441f@o4505765341102080.ingest.sentry.io/4505782666067968",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
)
# load config
args = parse()
config_handle = args.config
if config_handle is not None:
    config = Config(config_handle.name)
else:
    config = Config()

if __name__ == '__main__':
    # Use the SQLite DB file if we are running locally
    id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')
else:
    # Load the driver manager from local cache (if chrome_driver_install.py has been run
    os.environ['WDM_LOCAL'] = '1'
    # Use Google Cloud DB if we run on the cloud
    id_watch = GoogleCloudIdMaintainer(config)

configure_logging(config)

# initialize search plugins for config
config.init_searchers()

hunter = WebHunter(config, id_watch)

app.config["HUNTER"] = hunter
if config.has_website_config():
    app.secret_key = config.website_session_key()
    app.config["DOMAIN"] = config.website_domain()
    app.config["BOT_NAME"] = config.website_bot_name()
else:
    app.secret_key = b'Not a secret'
notifiers = config.notifiers()
if "telegram" in notifiers:
    app.config["BOT_TOKEN"] = config.telegram_bot_token()
if "mattermost" in notifiers:
    app.config["MM_WEBHOOK_URL"] = config.mattermost_webhook_url()

if __name__ == '__main__':
    listen = config['website'].get('listen', {})
    host = listen.get('host', '127.0.0.1')
    port = listen.get('port', '8080')
    app.run(host=host, port=port, debug=True)
