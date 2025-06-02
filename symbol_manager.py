import requests
import json
from difflib import get_close_matches
from config import MEXC_API

class SymbolManager:
    def __init__(self):
        self.symbols = []
        self.symbol_info = {}
        self._load_symbols()
    
    def _load_symbols(self):
        """Load all available MEXC futures symbols"""
        try:
            url = "https://contract.mexc.com/api/v1/contract/detail"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success', False):
                contracts = data.get('data', [])
                
                for contract in contracts:
                    symbol = contract.get('symbol')
                    if symbol and contract.get('state') == 0:  # Active contracts only
                        self.symbols.append(symbol)
                        self.symbol_info[symbol] = {
                            'display_name': contract.get('displayNameEn', symbol),
                            'base_coin': contract.get('baseCoin'),
                            'quote_coin': contract.get('quoteCoin'),
                            'contract_size': contract.get('contractSize'),
                            'min_leverage': contract.get('minLeverage'),
                            'max_leverage': contract.get('maxLeverage'),
                            'api_allowed': True  # Assume API allowed for active contracts
                        }
                
                print(f"Loaded {len(self.symbols)} active trading pairs from MEXC")
            else:
                print(f"Failed to load symbols: {data.get('message', 'Unknown error')}")
                # Fallback to default symbols
                self._load_default_symbols()
                
        except Exception as e:
            print(f"Error loading symbols from API: {str(e)}")
            self._load_default_symbols()
    
    def _load_default_symbols(self):
        """Load default symbols as fallback"""
        default_symbols = [
            'BTC_USDT', 'ETH_USDT', 'BNB_USDT', 'ADA_USDT', 'XRP_USDT',
            'SOL_USDT', 'DOT_USDT', 'DOGE_USDT', 'AVAX_USDT', 'MATIC_USDT',
            'LINK_USDT', 'UNI_USDT', 'LTC_USDT', 'BCH_USDT', 'ATOM_USDT'
        ]
        
        for symbol in default_symbols:
            self.symbols.append(symbol)
            self.symbol_info[symbol] = {
                'display_name': symbol,
                'base_coin': symbol.split('_')[0],
                'quote_coin': 'USDT',
                'api_allowed': True
            }
        
        print(f"Using {len(self.symbols)} default trading pairs")
    
    def get_all_symbols(self):
        """Get list of all available symbols"""
        return sorted(self.symbols)
    
    def validate_symbol(self, symbol):
        """Validate if symbol exists and is tradeable"""
        # Normalize symbol format
        normalized = self.normalize_symbol(symbol)
        
        if normalized in self.symbols:
            info = self.symbol_info.get(normalized, {})
            if info.get('api_allowed', True):
                return normalized, True, "Valid symbol"
            else:
                return normalized, False, "API trading not allowed for this symbol"
        
        return normalized, False, "Symbol not found"
    
    def normalize_symbol(self, symbol):
        """Normalize symbol format to MEXC standard"""
        symbol = symbol.upper().strip()
        
        # Handle different input formats
        if '_' not in symbol:
            # Try to add _USDT if it's just the base currency
            if symbol.endswith('USDT'):
                # Convert BTCUSDT to BTC_USDT
                base = symbol[:-4]
                symbol = f"{base}_USDT"
            else:
                # Add _USDT suffix
                symbol = f"{symbol}_USDT"
        
        return symbol
    
    def fuzzy_search(self, query, max_results=5):
        """Find symbols that closely match the query"""
        query = query.upper().strip()
        
        # Direct match first
        normalized = self.normalize_symbol(query)
        if normalized in self.symbols:
            return [normalized]
        
        # Fuzzy matching
        matches = []
        
        # Search in base currencies
        for symbol in self.symbols:
            base_coin = symbol.split('_')[0]
            if query in base_coin or base_coin.startswith(query):
                matches.append(symbol)
        
        # Use difflib for close matches
        if len(matches) < max_results:
            close_matches = get_close_matches(
                query, 
                [s.replace('_', '') for s in self.symbols], 
                n=max_results - len(matches),
                cutoff=0.6
            )
            
            for match in close_matches:
                # Convert back to underscore format
                for symbol in self.symbols:
                    if symbol.replace('_', '') == match and symbol not in matches:
                        matches.append(symbol)
                        break
        
        return matches[:max_results]
    
    def get_symbol_info(self, symbol):
        """Get detailed information about a symbol"""
        normalized = self.normalize_symbol(symbol)
        return self.symbol_info.get(normalized, {})
    
    def search_by_base_currency(self, base_currency):
        """Find all symbols for a specific base currency"""
        base_currency = base_currency.upper()
        matches = []
        
        for symbol in self.symbols:
            if symbol.startswith(f"{base_currency}_"):
                matches.append(symbol)
        
        return matches
    
    def get_popular_symbols(self, limit=20):
        """Get most popular trading pairs"""
        # Define popular symbols in order of preference
        popular_order = [
            'BTC_USDT', 'ETH_USDT', 'BNB_USDT', 'XRP_USDT', 'ADA_USDT',
            'SOL_USDT', 'DOT_USDT', 'DOGE_USDT', 'AVAX_USDT', 'MATIC_USDT',
            'LINK_USDT', 'UNI_USDT', 'LTC_USDT', 'BCH_USDT', 'ATOM_USDT',
            'FTM_USDT', 'NEAR_USDT', 'ALGO_USDT', 'VET_USDT', 'ICP_USDT'
        ]
        
        popular_symbols = []
        for symbol in popular_order:
            if symbol in self.symbols:
                popular_symbols.append(symbol)
                if len(popular_symbols) >= limit:
                    break
        
        # Fill remaining slots with other available symbols
        if len(popular_symbols) < limit:
            remaining = limit - len(popular_symbols)
            other_symbols = [s for s in self.symbols if s not in popular_symbols]
            popular_symbols.extend(other_symbols[:remaining])
        
        return popular_symbols
    
    def format_symbol_list(self, symbols, show_info=False):
        """Format symbol list for display"""
        if not symbols:
            return "No symbols found."
        
        output = []
        for symbol in symbols:
            if show_info:
                info = self.symbol_info.get(symbol, {})
                display_name = info.get('display_name', symbol)
                base_coin = info.get('base_coin', 'N/A')
                max_leverage = info.get('max_leverage', 'N/A')
                output.append(f"{symbol:<15} | {display_name:<20} | Base: {base_coin:<8} | Max Leverage: {max_leverage}")
            else:
                output.append(symbol)
        
        return '\n'.join(output)

# Global instance
symbol_manager = SymbolManager()
