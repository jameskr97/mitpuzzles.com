export interface EndpointCacheConfig {
  ttl_ms: number;
  log_prefix?: string;
}

/**
 * shared http cache using cache api
 * - single cache store for all api endpoints
 * - per-endpoint ttl config
 * - stale-while-offline support
 */
export class HTTPCache {
  readonly CACHE_NAME = 'mitpuzzles-cache-v1';
  private readonly _endpoint_configs = new Map<string, EndpointCacheConfig>();

  /** configure caching for a specific endpoint */
  configure_endpoint(api_endpoint: string, config: EndpointCacheConfig): void {
    this._endpoint_configs.set(api_endpoint, config);
  }

  /**
   * find base endpoint config for urls with query params and subpaths
   * e.g. /api/puzzle/freeplay/leaderboard?type=sudoku -> /api/puzzle/freeplay/leaderboard
   * e.g. /api/puzzle/definition/123/ -> /api/puzzle/definition
   */
  private find_base_endpoint_config(full_url: string): EndpointCacheConfig | null {
    const base_url = full_url.split('?')[0]; // remove query params
    
    // First try exact match
    const exactMatch = this._endpoint_configs.get(base_url);
    if (exactMatch) return exactMatch;
    
    // Try prefix matching for subpaths
    for (const [configPath, config] of this._endpoint_configs) {
      if (base_url.startsWith(configPath + '/') || base_url.startsWith(configPath)) {
        return config;
      }
    }
    
    return null;
  }

  /** get data. check cache first, the ensure within TTL. otherwise, fetch. */
  async get<T = any>(api_endpoint: string): Promise<T> {
    const config = this.find_base_endpoint_config(api_endpoint);
    if (!config) throw new Error(`Endpoint ${api_endpoint} not configured. Call configure_endpoint() first.`);
    // invariant - config exists for endpoint

    const cache = await caches.open(this.CACHE_NAME);
    const log_prefix = config.log_prefix || `[HTTPCache:${api_endpoint}]`;

    // check if cache is valid
    const cached_response = await cache.match(api_endpoint);
    fetch_break: if (cached_response && cached_response.ok) {

      // ensure we're not stale
      if (await this.is_cache_stale(api_endpoint)) {
        // console.log(`${log_prefix} Cache expired, fetching fresh data`);
        break fetch_break;
      }

      // try loading cached data
      try {
        const data = await cached_response.json();
        // console.log(`${log_prefix} Using fresh cached data`);
        return data;
      } catch (error) {
        // console.warn(`${log_prefix} Failed to parse cached data:`, error);
        break fetch_break;
      }
    }
    
    // Fetch from network
    try {
      const response = await fetch(api_endpoint);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Add timestamp to response before caching
      const response_with_timestamp = new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          ...Object.fromEntries(response.headers.entries()),
          'x-cache-timestamp': Date.now().toString(),
          'content-type': response.headers.get('content-type') || 'application/json'
        }
      });
      
      await cache.put(api_endpoint, response_with_timestamp.clone());
      const data = await response_with_timestamp.json();
      // console.log(`${log_prefix} Fetched and cached fresh data`);
      return data;
      
    } catch (error) {
      // Network failed, use stale cache if available
      if (cached_response) {
        // console.warn(`${log_prefix} Network failed, using stale cache`);
        try {
          return await cached_response.json();
        } catch (parse_error) {
          // console.error(`${log_prefix} Failed to parse stale cache:`, parse_error);
        }
      }
      
      throw new Error(`${log_prefix} No cached data available and network request failed: ${error}`);
    }
  }

  /** force refresh from network and update cache */
  async refresh<T = any>(api_endpoint: string): Promise<T> {
    const config = this.find_base_endpoint_config(api_endpoint)
    if (!config) throw new Error(`Endpoint ${api_endpoint} not configured. Call configure_endpoint() first.`);
    // invariant - config exists for endpoint

    const cache = await caches.open(this.CACHE_NAME);
    const log_prefix = config.log_prefix || `[HTTPCache:${api_endpoint}]`;
    
    try {
      // request from network
      const response = await fetch(api_endpoint);
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

      // add timestamp to response before caching
      const response_with_timestamp = new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          ...Object.fromEntries(response.headers.entries()),
          'x-cache-timestamp': Date.now().toString(),
          'content-type': response.headers.get('content-type') || 'application/json'
        }
      });
      
      await cache.put(api_endpoint, response_with_timestamp.clone());
      const data = await response_with_timestamp.json();
      console.log(`${log_prefix} Force refreshed data`);
      return data;
      
    } catch (error) {
      console.error(`${log_prefix} Failed to refresh:`, error);
      throw error;
    }
  }

  /** clear cached data for specific endpoint */
  async clear(api_endpoint: string): Promise<void> {
    const config = this._endpoint_configs.get(api_endpoint);
    const log_prefix = config?.log_prefix || `[HTTPCache:${api_endpoint}]`;

    const cache = await caches.open(this.CACHE_NAME);
    const deleted = await cache.delete(api_endpoint);
    
    if (deleted) {
      console.log(`${log_prefix} Cache cleared`);
    } else {
      console.warn(`${log_prefix} No cached data found to clear`);
    }
  }

  /** get cache age in milliseconds for endpoint */
  async get_cache_age(api_endpoint: string): Promise<number | null> {
    const cache = await caches.open(this.CACHE_NAME);
    const cached_response = await cache.match(api_endpoint);
    if (!cached_response) return null;
    
    const cache_timestamp = cached_response.headers.get('x-cache-timestamp');
    if (!cache_timestamp) return null;

    return Date.now() - parseInt(cache_timestamp);
  }

  /** check if cache is stale for endpoint */
  async is_cache_stale(api_endpoint: string): Promise<boolean> {
    const config = this.find_base_endpoint_config(api_endpoint)
    if (!config) return true;

    const age_ms = await this.get_cache_age(api_endpoint);
    if (!age_ms) return true;

    // console.log(`[HTTPCache:${api_endpoint}] Cache age: ${age_ms} ms, TTL: ${config.ttl_ms} ms`);
    return age_ms > config.ttl_ms;
  }

}

// Singleton instance for easy import
export const shared_http_cache = new HTTPCache();

export const init_cached_endpoints = () => {
  const CACHED_ENDPOINTS: Record<string, any> = {
    '/api/puzzle/definition/types': { ttl_ms: 24 * 60 * 60 * 1000, log_prefix: '[PuzzleTypesCatalog]' }, // 24 hours
    '/api/puzzle/freeplay/leaderboard': { ttl_ms: 5 * 60 * 1000, log_prefix: '[FreeplayLeaderboard]' }, // 5 minutes
    '/api/puzzle/definition': { ttl_ms: 5 * 60 * 1000, log_prefix: '[PuzzleDefinition]' }, // 5 minutes for testing
  };

  // register all endpoints
  Object.keys(CACHED_ENDPOINTS).forEach((key) => shared_http_cache.configure_endpoint(key, CACHED_ENDPOINTS[key]));
}
