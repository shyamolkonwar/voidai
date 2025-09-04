/**
 * Server health check utilities
 */

export interface ServerStatus {
  isOnline: boolean;
  lastChecked: Date | null;
  error?: string;
}

/**
 * Check if the backend server is online and responding
 */
export async function checkServerHealth(): Promise<ServerStatus> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    const response = await fetch('http://127.0.0.1:8001/health', {
      method: 'GET',
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      return {
        isOnline: true,
        lastChecked: new Date(),
      };
    } else {
      return {
        isOnline: false,
        lastChecked: new Date(),
        error: `Server returned status: ${response.status}`,
      };
    }
  } catch (error) {
    return {
      isOnline: false,
      lastChecked: new Date(),
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Check if the server is ready for chat operations
 * This includes checking both the main API and session endpoints
 */
export async function checkServerReady(): Promise<ServerStatus> {
  try {
    // Check both health endpoint and session endpoint
    const [healthResponse, sessionResponse] = await Promise.allSettled([
      fetch('http://127.0.0.1:8001/health', { method: 'GET' }),
      fetch('http://127.0.0.1:8001/api/v1/sessions', { method: 'GET' }),
    ]);
    
    const isHealthOk = healthResponse.status === 'fulfilled' && healthResponse.value.ok;
    const isSessionOk = sessionResponse.status === 'fulfilled' && sessionResponse.value.ok;
    
    if (isHealthOk && isSessionOk) {
      return {
        isOnline: true,
        lastChecked: new Date(),
      };
    } else {
      const errors = [];
      if (healthResponse.status === 'rejected') errors.push('Health endpoint unreachable');
      else if (!healthResponse.value.ok) errors.push(`Health endpoint: ${healthResponse.value.status}`);
      
      if (sessionResponse.status === 'rejected') errors.push('Session endpoint unreachable');
      else if (!sessionResponse.value.ok) errors.push(`Session endpoint: ${sessionResponse.value.status}`);
      
      return {
        isOnline: false,
        lastChecked: new Date(),
        error: errors.join(', '),
      };
    }
  } catch (error) {
    return {
      isOnline: false,
      lastChecked: new Date(),
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}