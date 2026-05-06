"""Kite Connect API client for Zerodha integration.

Provides real-time data, order management, and position tracking
for Indian markets through Zerodha's Kite Connect API.
"""

import os
import time
from datetime import datetime, date
from typing import Optional, Dict, List, Any
import logging

try:
    from kiteconnect import KiteConnect, KiteTicker
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    logging.warning("kiteconnect not installed. Install with: pip install kiteconnect")

from tradingagents.default_config import DEFAULT_CONFIG


class KiteClient:
    """Wrapper for Zerodha Kite Connect API with authentication and data fetching."""
    
    def __init__(self, api_key: str = None, api_secret: str = None, access_token: str = None):
        """Initialize Kite client with credentials.
        
        Args:
            api_key: Kite API key (from .env or config)
            api_secret: Kite API secret (from .env or config)  
            access_token: Kite access token (from .env or config)
        """
        if not KITE_AVAILABLE:
            raise ImportError("kiteconnect package is required. Install with: pip install kiteconnect")
        
        self.api_key = api_key or os.getenv("KITE_API_KEY") or DEFAULT_CONFIG.get("kite_api_key")
        self.api_secret = api_secret or os.getenv("KITE_API_SECRET") or DEFAULT_CONFIG.get("kite_api_secret")
        self.access_token = access_token or os.getenv("KITE_ACCESS_TOKEN") or DEFAULT_CONFIG.get("kite_access_token")
        
        if not all([self.api_key, self.api_secret]):
            raise ValueError("Kite API key and secret are required. Set KITE_API_KEY and KITE_API_SECRET in .env")
        
        self.kite = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Kite Connect client with access token."""
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                logging.info("Kite client initialized with existing access token")
            else:
                logging.warning("No access token provided. Use generate_access_token() to authenticate.")
                
        except Exception as e:
            logging.error(f"Failed to initialize Kite client: {e}")
            raise
    
    def generate_access_token(self, request_token: str) -> str:
        """Generate access token from request token.
        
        Args:
            request_token: Request token obtained after user authorization
            
        Returns:
            Access token string
        """
        try:
            data = self.kite.generate_session(request_token, self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            
            # Save to environment for future use
            os.environ["KITE_ACCESS_TOKEN"] = self.access_token
            
            logging.info("Access token generated successfully")
            return self.access_token
            
        except Exception as e:
            logging.error(f"Failed to generate access token: {e}")
            raise
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        if not self.kite:
            self._initialize_client()
        
        try:
            return self.kite.profile()
        except Exception as e:
            logging.error(f"Failed to get profile: {e}")
            return {}
    
    def get_holdings(self) -> List[Dict[str, Any]]:
        """Get current holdings."""
        if not self.kite:
            self._initialize_client()
        
        try:
            return self.kite.holdings()
        except Exception as e:
            logging.error(f"Failed to get holdings: {e}")
            return []
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions."""
        if not self.kite:
            self._initialize_client()
        
        try:
            return self.kite.positions()
        except Exception as e:
            logging.error(f"Failed to get positions: {e}")
            return {}
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get order history."""
        if not self.kite:
            self._initialize_client()
        
        try:
            return self.kite.orders()
        except Exception as e:
            logging.error(f"Failed to get orders: {e}")
            return []
    
    def get_instruments(self, exchange: str = "NSE") -> List[Dict[str, Any]]:
        """Get trading instruments for an exchange.
        
        Args:
            exchange: Exchange name (NSE, BSE, etc.)
            
        Returns:
            List of instrument dictionaries
        """
        if not self.kite:
            self._initialize_client()
        
        try:
            return self.kite.instruments(exchange)
        except Exception as e:
            logging.error(f"Failed to get instruments for {exchange}: {e}")
            return []
    
    def get_quote(self, instrument_token: str = None, tradingsymbol: str = None) -> Dict[str, Any]:
        """Get quote for an instrument.
        
        Args:
            instrument_token: Kite instrument token
            tradingsymbol: Trading symbol (e.g., "RELIANCE")
            
        Returns:
            Quote dictionary
        """
        if not self.kite:
            self._initialize_client()
        
        try:
            if tradingsymbol:
                # Get instrument token from symbol first
                instruments = self.get_instruments()
                for inst in instruments:
                    if inst.get("tradingsymbol") == tradingsymbol:
                        instrument_token = inst["instrument_token"]
                        break
            
            if instrument_token:
                return self.kite.quote(instrument_token)
            else:
                return {}
                
        except Exception as e:
            logging.error(f"Failed to get quote: {e}")
            return {}
    
    def get_historical_data(
        self, 
        instrument_token: str = None,
        tradingsymbol: str = None,
        from_date: date = None,
        to_date: date = None,
        interval: str = "day"
    ) -> List[Dict[str, Any]]:
        """Get historical data for an instrument.
        
        Args:
            instrument_token: Kite instrument token
            tradingsymbol: Trading symbol (e.g., "RELIANCE")
            from_date: Start date
            to_date: End date  
            interval: Data interval (minute, day, 5minute, etc.)
            
        Returns:
            List of historical data dictionaries
        """
        if not self.kite:
            self._initialize_client()
        
        try:
            if tradingsymbol and not instrument_token:
                # Get instrument token from symbol
                instruments = self.get_instruments()
                for inst in instruments:
                    if inst.get("tradingsymbol") == tradingsymbol:
                        instrument_token = inst["instrument_token"]
                        break
            
            if instrument_token:
                return self.kite.historical_data(
                    instrument_token, 
                    from_date, 
                    to_date, 
                    interval
                )
            else:
                return []
                
        except Exception as e:
            logging.error(f"Failed to get historical data: {e}")
            return []
    
    def place_order(
        self,
        tradingsymbol: str,
        exchange: str = "NSE",
        transaction_type: str = "BUY",
        quantity: int = 1,
        order_type: str = "MARKET",
        product: str = "CNC",
        price: float = None,
        trigger_price: float = None
    ) -> Dict[str, Any]:
        """Place an order.
        
        Args:
            tradingsymbol: Trading symbol
            exchange: Exchange name
            transaction_type: BUY or SELL
            quantity: Number of shares
            order_type: MARKET, LIMIT, SL, SL-M
            product: CNC, MIS, NRML
            price: Limit price (for LIMIT orders)
            trigger_price: Trigger price (for SL, SL-M orders)
            
        Returns:
            Order response dictionary
        """
        if not self.kite:
            self._initialize_client()
        
        # Check if dry run mode is enabled
        if not DEFAULT_CONFIG.get("order_execution_enabled", False):
            logging.info(f"DRY RUN: Would place {transaction_type} order for {quantity} shares of {tradingsymbol}")
            return {
                "status": "DRY_RUN",
                "message": f"DRY RUN: {transaction_type} {quantity} shares of {tradingsymbol} at {order_type}",
                "tradingsymbol": tradingsymbol,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type
            }
        
        try:
            order_params = {
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product,
            }
            
            if price:
                order_params["price"] = price
            if trigger_price:
                order_params["trigger_price"] = trigger_price
            
            return self.kite.place_order(**order_params)
            
        except Exception as e:
            logging.error(f"Failed to place order: {e}")
            return {"status": "ERROR", "message": str(e)}
    
    def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify an existing order."""
        if not self.kite:
            self._initialize_client()
        
        try:
            return self.kite.modify_order(order_id, **kwargs)
        except Exception as e:
            logging.error(f"Failed to modify order {order_id}: {e}")
            return {"status": "ERROR", "message": str(e)}
    
    def cancel_order(self, order_id: str, variety: str = "regular") -> Dict[str, Any]:
        """Cancel an order."""
        if not self.kite:
            self._initialize_client()
        
        try:
            return self.kite.cancel_order(order_id, variety)
        except Exception as e:
            logging.error(f"Failed to cancel order {order_id}: {e}")
            return {"status": "ERROR", "message": str(e)}
    
    def get_margins(self) -> Dict[str, Any]:
        """Get margin details."""
        if not self.kite:
            self._initialize_client()
        
        try:
            return self.kite.margins()
        except Exception as e:
            logging.error(f"Failed to get margins: {e}")
            return {}


# Global instance for reuse
_kite_client = None

def get_kite_client() -> Optional[KiteClient]:
    """Get or create global Kite client instance."""
    global _kite_client
    
    if _kite_client is None:
        try:
            _kite_client = KiteClient()
        except Exception as e:
            logging.error(f"Failed to create Kite client: {e}")
            _kite_client = None
    
    return _kite_client


def is_kite_available() -> bool:
    """Check if Kite Connect is available and configured."""
    return (
        KITE_AVAILABLE and 
        os.getenv("KITE_API_KEY") and 
        (os.getenv("KITE_ACCESS_TOKEN") or os.getenv("KITE_API_SECRET"))
    )
