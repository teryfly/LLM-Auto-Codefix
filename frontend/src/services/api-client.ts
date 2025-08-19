class APIClient {
  private baseURL: string;
  
  constructor(baseURL: string = 'http://192.168.120.111:8001/api/v1') {
    this.baseURL = baseURL;
  }

  async request(endpoint: string, options: RequestInit = {}): Promise {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        timeout: 30000, // 30秒超时
        ...options,
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.detail || errorMessage;
        } catch {
          // 如果无法解析JSON，使用默认错误消息
        }
        
        // 根据状态码提供更友好的错误消息
        if (response.status === 0 || response.status >= 500) {
          throw new Error(`Backend service unavailable. Please check if the server is running. (${errorMessage})`);
        } else if (response.status === 404) {
          throw new Error(`Resource not found: ${errorMessage}`);
        } else if (response.status === 403) {
          throw new Error(`Access denied: ${errorMessage}`);
        } else if (response.status === 401) {
          throw new Error(`Authentication failed: ${errorMessage}`);
        } else {
          throw new Error(errorMessage);
        }
      }

      return response.json();
    } catch (error) {
      // 网络错误或其他连接问题
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to backend service. Please check if the server is running and accessible.');
      }
      
      // 超时错误
      if (error.name === 'AbortError' || error.message.includes('timeout')) {
        throw new Error('Request timeout. The server may be overloaded or unresponsive.');
      }
      
      // 重新抛出已处理的错误
      throw error;
    }
  }

  async get(endpoint: string): Promise {
    return this.request(endpoint);
  }

  async post(endpoint: string, data?: any): Promise {
    return this.request(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put(endpoint: string, data?: any): Promise {
    return this.request(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete(endpoint: string): Promise {
    return this.request(endpoint, {
      method: 'DELETE',
    });
  }

  // 健康检查方法
  async healthCheck(): Promise {
    try {
      await this.get('/health');
      return true;
    } catch {
      return false;
    }
  }
}

export const apiClient = new APIClient();