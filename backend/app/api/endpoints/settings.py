from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from loguru import logger

from ...database import get_db
from ...db.repos.settings_repository import SettingsRepository
from ...utils import server_error, database_error

router = APIRouter(tags=["settings"])


@router.get("/settings")
async def get_settings(db: Session = Depends(get_db)) -> Dict:
    try:
        settings_dict = SettingsRepository.get_settings_dict(db)
        return {
            'success': True,
            'data': settings_dict
        }
    except Exception as e:
        raise server_error(e, "fetching settings")


@router.put("/settings")
async def update_settings(
    settings_update: Dict,
    db: Session = Depends(get_db)
) -> Dict:
    try:
        update_data = {}
        
        if 'data_api' in settings_update:
            data_api = settings_update['data_api']
            if 'refresh_interval' in data_api:
                update_data['data_refresh_interval'] = data_api['refresh_interval']
            if 'active_providers' in data_api:
                update_data['active_providers'] = data_api['active_providers']
            
            if 'alpaca_api_key' in data_api and not SettingsRepository._is_masked_key(data_api['alpaca_api_key']):
                update_data['alpaca_api_key'] = SettingsRepository.encode_api_key(data_api['alpaca_api_key'])
            if 'alpaca_secret_key' in data_api and not SettingsRepository._is_masked_key(data_api['alpaca_secret_key']):
                update_data['alpaca_secret_key'] = SettingsRepository.encode_api_key(data_api['alpaca_secret_key'])
            if 'alpha_vantage_api_key' in data_api and not SettingsRepository._is_masked_key(data_api['alpha_vantage_api_key']):
                update_data['alpha_vantage_api_key'] = SettingsRepository.encode_api_key(data_api['alpha_vantage_api_key'])
            if 'polygon_api_key' in data_api and not SettingsRepository._is_masked_key(data_api['polygon_api_key']):
                update_data['polygon_api_key'] = SettingsRepository.encode_api_key(data_api['polygon_api_key'])
            if 'coinbase_api_key' in data_api and not SettingsRepository._is_masked_key(data_api['coinbase_api_key']):
                update_data['coinbase_api_key'] = SettingsRepository.encode_api_key(data_api['coinbase_api_key'])
            if 'coinbase_api_secret' in data_api and not SettingsRepository._is_masked_key(data_api['coinbase_api_secret']):
                update_data['coinbase_api_secret'] = SettingsRepository.encode_api_key(data_api['coinbase_api_secret'])
        
        if 'trading_controls' in settings_update:
            trading = settings_update['trading_controls']
            if 'paper_trading' in trading:
                update_data['paper_trading'] = trading['paper_trading']
            if 'enable_auto_trading' in trading:
                update_data['enable_auto_trading'] = trading['enable_auto_trading']
                logger.warning(f"Auto-trading {'ENABLED' if trading['enable_auto_trading'] else 'DISABLED'}")
            if 'max_position_size' in trading:
                update_data['max_position_size'] = trading['max_position_size']
            if 'max_daily_loss' in trading:
                update_data['max_daily_loss'] = trading['max_daily_loss']
            if 'stop_loss_pct' in trading:
                update_data['stop_loss_pct'] = trading['stop_loss_pct']
        
        if 'ai_config' in settings_update:
            ai_config = settings_update['ai_config']
            if 'agent_weights' in ai_config:
                update_data['agent_weights'] = ai_config['agent_weights']
            if 'analysis_cadence' in ai_config:
                update_data['analysis_cadence'] = ai_config['analysis_cadence']
        
        if 'display' in settings_update:
            display = settings_update['display']
            if 'theme' in display:
                update_data['theme'] = display['theme']
            if 'layout_density' in display:
                update_data['layout_density'] = display['layout_density']
            if 'show_news_ticker' in display:
                update_data['show_news_ticker'] = display['show_news_ticker']
        
        updated_settings_obj = SettingsRepository.update_settings(db, **update_data)
        
        SettingsRepository.update_env_from_settings(updated_settings_obj)
        
        updated_settings = SettingsRepository.get_settings_dict(db)
        
        logger.info(f"Settings updated: {list(update_data.keys())}")
        
        return {
            'success': True,
            'message': 'Settings updated successfully',
            'data': updated_settings
        }
    except Exception as e:
        raise database_error(e, "updating settings")
