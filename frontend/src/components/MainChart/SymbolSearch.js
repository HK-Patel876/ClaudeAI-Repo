import React, { useState, useEffect, useRef } from 'react';
import './SymbolSearch.css';

const SymbolSearch = ({ currentSymbol, onSymbolChange }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const searchRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const searchSymbols = async () => {
      if (searchQuery.length === 0) {
        const response = await fetch('/api/v1/data/symbols/search');
        const data = await response.json();
        setSearchResults(data);
      } else {
        const response = await fetch(`/api/v1/data/symbols/search?q=${searchQuery}`);
        const data = await response.json();
        setSearchResults(data);
      }
    };

    const debounce = setTimeout(() => {
      if (isOpen) {
        searchSymbols();
      }
    }, 300);

    return () => clearTimeout(debounce);
  }, [searchQuery, isOpen]);

  const handleSymbolSelect = (symbol) => {
    onSymbolChange(symbol);
    setSearchQuery('');
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  return (
    <div className="symbol-search" ref={searchRef}>
      <div className="search-input-wrapper">
        <input
          type="text"
          className="search-input"
          placeholder="Search symbols..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={handleInputFocus}
        />
        <span className="search-icon">🔍</span>
      </div>

      {isOpen && (
        <div className="search-dropdown">
          <div className="search-results">
            {searchResults.length > 0 ? (
              searchResults.map((symbol) => (
                <div
                  key={symbol}
                  className={`search-result-item ${symbol === currentSymbol ? 'active' : ''}`}
                  onClick={() => handleSymbolSelect(symbol)}
                >
                  <span className="symbol-name">{symbol}</span>
                  {symbol === currentSymbol && <span className="current-badge">Current</span>}
                </div>
              ))
            ) : (
              <div className="no-results">No symbols found</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SymbolSearch;
