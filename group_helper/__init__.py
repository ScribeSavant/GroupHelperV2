import telegram.ext as tg
from telethon import TelegramClient
from json import load
import logging
import sys
import yaml
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Set, Any
import os
from dotenv import load_dotenv

load_dotenv('config.env')


class GroupHelperConfig:
    def __init__(self, *args, **kwargs) -> None:
        """
        group_helper configuration class
        """
        self.api_id: int = kwargs.get('API_ID', None)
        self.api_hash: str = kwargs.get('API_HASH', None)
        self.bot_token: str = kwargs.get('BOT_TOKEN', None)
        self.DATABASE_URL: str = kwargs.get('DATABASE_URL', None)
        self.load: List[str] = kwargs.get('LOAD', list())
        self.no_load: List[str] = kwargs.get('NO_LOAD', list())
        self.del_cmds: Optional[bool] = kwargs.get('DEL_CMDS', False)
        self.strict_antispam: Optional[bool] = kwargs.get(
            'STRICT_ANTISPAM', False)
        self.workers: Optional[int] = kwargs.get('WORKERS', 4)
        self.owner_id: int = kwargs.get('OWNER_ID', None)
        self.sudo_users: Set[int] = kwargs.get('SUDO_USERS', set())
        self.whitelist_users: Set[int] = kwargs.get('WHITELIST_USERS', set())
        self.message_dump: Optional[int] = kwargs.get('MESSAGE_DUMP', 0)
        self.spamwatch_api: Optional[str] = kwargs.get('SPAMWATCH_API', "")
        self.spamwatch_client: Optional[Any] = None
        self.telethon_client: Optional[Any] = None
        self.updater: Optional[Any] = None
        self.dispatcher: Optional[Any] = None


logging.basicConfig(
    format="[%(levelname)s %(asctime)s] Module '%(module)s', function '%(funcName)s' at line %(lineno)d -> %(message)s",
    level=logging.INFO)
logging.info("Starting group_helper...")

if sys.version_info < (3, 8, 0):
    logging.error(
        "Your Python version is too old for group_helper to run, please update to Python 3.8 or above"
    )
    exit(1)

try:
    config_file = dict(os.environ)
    config_file['LOAD'] = config_file['LOAD'].split()
    config_file['NO_LOAD'] = config_file['NO_LOAD'].split()
    config_file['SUDO_USERS'] = config_file['SUDO_USERS'].split()
    config_file['WHITELIST_USERS'] = config_file['WHITELIST_USERS'].split()
except Exception as error:
    logging.error(
        f"Could not load config file due to a {type(error).__name__}: {error}")
    exit(1)

try:
    CONFIG = GroupHelperConfig(**config_file)
except ValidationError as validation_error:
    logging.error(
        f"Something went wrong when parsing config.yml: {validation_error}")
    exit(1)

CONFIG.sudo_users.append(CONFIG.owner_id)

try:
    CONFIG.updater = tg.Updater(CONFIG.bot_token, workers=int(CONFIG.workers))
    CONFIG.dispatcher = CONFIG.updater.dispatcher
    CONFIG.telethon_client = TelegramClient("group_helper", CONFIG.api_id,
                                            CONFIG.api_hash)

    # We import it now to ensure that all previous variables have been set
    from group_helper.modules.helper_funcs.handlers import CustomCommandHandler, CustomMessageHandler
    tg.CommandHandler = CustomCommandHandler
    tg.MessageHandler = CustomMessageHandler
except Exception as telegram_error:
    logging.error(
        f"Could not initialize Telegram client due to a {type(telegram_error).__name__}: {telegram_error}"
    )
    exit(1)
