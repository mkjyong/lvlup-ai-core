import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  // 쿠키(리프레시 토큰) 전송을 위해 필요
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    // eslint-disable-next-line no-param-reassign
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// handle 401 and refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else {
      // @ts-ignore
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            // eslint-disable-next-line no-param-reassign
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true; // custom flag
      isRefreshing = true;
      try {
        // 백엔드 리프레시 토큰 엔드포인트에 맞춰 경로 수정
        const res = await api.post<{ access_token: string }>('/auth/refresh');
        const newToken = res.data.access_token;
        localStorage.setItem('token', newToken);
        processQueue(null, newToken);
        // eslint-disable-next-line no-param-reassign
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        window.location.href = '/auth';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  },
);

export default api;

// --------------------
// Game-specific helper APIs
// --------------------

export const fetchGameIds = async (): Promise<Record<string, { account_id: string; region?: string }>> => {
  const { data } = await api.get('/user/game-ids');
  return data;
};

export const patchGameIds = async (payload: Record<string, { account_id: string; region?: string }>) => {
  await api.patch('/user/game-ids', payload);
};

export const fetchStatsOverview = async (
  game: string,
  period: 'weekly' | 'monthly' = 'weekly',
): Promise<{ metrics: Record<string, number>; percentile: Record<string, number> }> => {
  const { data } = await api.get('/stats/overview', { params: { game, period } });
  return data;
};

export const fetchStatsTrend = async (
  game: string,
  metric: string,
  weeks = 8,
): Promise<{ trend: Array<[string, number]> }> => {
  const { data } = await api.get('/stats/trend', { params: { game, metric, weeks } });
  return data;
}; 