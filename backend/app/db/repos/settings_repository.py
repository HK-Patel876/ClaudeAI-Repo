from typing import Optional, Dict
from sqlalchemy.orm import Session
from loguru import logger
from cryptography.fernet import Fernet
import os
from pathlib import Path

from ...models.database_models import UserSettings


def _get_or_generate_encryption_key():
    """Get encryption key from environment or generate and persist one."""
    key = os.getenv('ENCRYPTION_KEY')
    
    if key:
        # Validate the key format
        try:
            Fernet(key.encode() if isinstance(key, str) else key)
            logger.info("Using ENCRYPTION_KEY from environment")
            return key.encode() if isinstance(key, str) else key
        except Exception as e:
            logger.warning(f"Invalid ENCRYPTION_KEY format in environment: {e}. Generating a new key.")
            # Fall through to generate new key
    
    # Generate new key
    new_key = Fernet.generate_key()
    
    # Persist to .env file
    env_file = Path('.env')
    try:
        # Check if .env exists and if ENCRYPTION_KEY is already in it
        existing_content = ""
        if env_file.exists():
            existing_content = env_file.read_text()
            
        # Only append if ENCRYPTION_KEY is not already in the file
        if 'ENCRYPTION_KEY=' not in existing_content:
            with env_file.open('a') as f:
                # Add a newline before if file exists and doesn't end with newline
                if existing_content and not existing_content.endswith('\n'):
                    f.write('\n')
                # Quote the value to preserve special characters like trailing =
                f.write(f'ENCRYPTION_KEY="{new_key.decode()}"\n')
            logger.info("Generated and persisted new encryption key to .env file")
        else:
            logger.info("ENCRYPTION_KEY already exists in .env file")
    except Exception as e:
        logger.error(f"Failed to persist encryption key to .env: {e}")
        logger.warning("Encryption key will be lost on restart! Please set ENCRYPTION_KEY manually in .env file.")
    
    return new_key


# Get or generate encryption key (persisted to .env if generated)
ENCRYPTION_KEY = _get_or_generate_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)


class SettingsRepository:
    
    @staticmethod
    def get_settings(db: Session, user_id: str = "default") -> Optional[UserSettings]:
        return db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()
    
    @staticmethod
    def get_or_create_settings(db: Session, user_id: str = "default") -> UserSettings:
        settings = SettingsRepository.get_settings(db, user_id)
        if not settings:
            settings = UserSettings(
                user_id=user_id,
                data_refresh_interval=10,
                active_providers=['demo'],
                paper_trading=True,
                max_position_size=0.1,
                max_daily_loss=0.05,
                stop_loss_pct=0.02,
                agent_weights={
                    'technical': 1.0,
                    'news': 1.0,
                    'fundamental': 1.0,
                    'risk': 1.5
                },
                analysis_cadence=60,
                theme='dark',
                layout_density='comfortable',
                show_news_ticker=True
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
            logger.info(f"Created default settings for user {user_id}")
        return settings
    
    @staticmethod
    def update_settings(
        db: Session,
        user_id: str = "default",
        **kwargs
    ) -> UserSettings:
        settings = SettingsRepository.get_or_create_settings(db, user_id)
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        db.commit()
        db.refresh(settings)
        logger.info(f"Updated settings for user {user_id}")
        return settings
    
    @staticmethod
    def _encrypt(value: str) -> str:
        if not value:
            return None
        try:
            return cipher_suite.encrypt(value.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return None
    
    @staticmethod
    def _decrypt(value: str) -> str:
        if not value:
            return None
        try:
            return cipher_suite.decrypt(value.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None
    
    @staticmethod
    def _mask_key(encrypted_key: str) -> str:
        if not encrypted_key:
            return None
        decrypted = SettingsRepository._decrypt(encrypted_key)
        if not decrypted:
            return None
        if len(decrypted) < 4:
            return "****"
        return "•" * (len(decrypted) - 4) + decrypted[-4:]
    
    @staticmethod
    def _is_masked_key(key: str) -> bool:
        if not key:
            return False
        return key.startswith("•") or key == "****"
    
    @staticmethod
    def get_settings_dict(db: Session, user_id: str = "default") -> Dict:
        settings = SettingsRepository.get_or_create_settings(db, user_id)
        
        return {
            'data_api': {
                'refresh_interval': settings.data_refresh_interval,
                'active_providers': settings.active_providers or [],
                'alpaca_api_key': SettingsRepository._mask_key(settings.alpaca_api_key),
                'alpaca_secret_key': SettingsRepository._mask_key(settings.alpaca_secret_key),
                'alpha_vantage_api_key': SettingsRepository._mask_key(settings.alpha_vantage_api_key),
                'polygon_api_key': SettingsRepository._mask_key(settings.polygon_api_key),
                'coinbase_api_key': SettingsRepository._mask_key(settings.coinbase_api_key),
                'coinbase_api_secret': SettingsRepository._mask_key(settings.coinbase_api_secret)
            },
            'trading_controls': {
                'paper_trading': settings.paper_trading,
                'enable_auto_trading': settings.enable_auto_trading,
                'max_position_size': settings.max_position_size,
                'max_daily_loss': settings.max_daily_loss,
                'stop_loss_pct': settings.stop_loss_pct
            },
            'ai_config': {
                'agent_weights': settings.agent_weights or {},
                'analysis_cadence': settings.analysis_cadence
            },
            'display': {
                'theme': settings.theme,
                'layout_density': settings.layout_density,
                'show_news_ticker': settings.show_news_ticker
            }
        }
    
    @staticmethod
    def encode_api_key(key: str) -> str:
        if not key or SettingsRepository._is_masked_key(key):
            return None
        return SettingsRepository._encrypt(key)
    
    @staticmethod
    def decode_api_key(encrypted_key: str) -> str:
        return SettingsRepository._decrypt(encrypted_key)
    
    @staticmethod
    def update_env_from_settings(settings: UserSettings):
        if settings.alpaca_api_key:
            os.environ['ALPACA_API_KEY'] = SettingsRepository._decrypt(settings.alpaca_api_key) or ''
        if settings.alpaca_secret_key:
            os.environ['ALPACA_SECRET_KEY'] = SettingsRepository._decrypt(settings.alpaca_secret_key) or ''
        if settings.alpha_vantage_api_key:
            os.environ['ALPHA_VANTAGE_API_KEY'] = SettingsRepository._decrypt(settings.alpha_vantage_api_key) or ''
        if settings.polygon_api_key:
            os.environ['POLYGON_API_KEY'] = SettingsRepository._decrypt(settings.polygon_api_key) or ''
        if settings.coinbase_api_key:
            os.environ['COINBASE_API_KEY'] = SettingsRepository._decrypt(settings.coinbase_api_key) or ''
        if settings.coinbase_api_secret:
            os.environ['COINBASE_API_SECRET'] = SettingsRepository._decrypt(settings.coinbase_api_secret) or ''
        logger.info("Updated environment variables from settings")
