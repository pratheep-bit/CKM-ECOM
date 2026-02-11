import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Request interceptor to add auth token
        this.client.interceptors.request.use(
            (config: InternalAxiosRequestConfig) => {
                const token = localStorage.getItem('access_token');
                if (token && config.headers) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor to handle token refresh
        this.client.interceptors.response.use(
            (response) => response,
            async (error) => {
                const originalRequest = error.config;

                if (error.response?.status === 401 && !originalRequest._retry) {
                    originalRequest._retry = true;

                    try {
                        const refreshToken = localStorage.getItem('refresh_token');
                        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
                            refresh_token: refreshToken,
                        });

                        const { access_token, refresh_token: new_refresh_token } = response.data;
                        localStorage.setItem('access_token', access_token);
                        if (new_refresh_token) {
                            localStorage.setItem('refresh_token', new_refresh_token);
                        }

                        originalRequest.headers.Authorization = `Bearer ${access_token}`;
                        return this.client(originalRequest);
                    } catch (refreshError) {
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        window.location.href = '/login';
                        return Promise.reject(refreshError);
                    }
                }

                return Promise.reject(error);
            }
        );
    }

    // Auth endpoints
    async sendOTP(mobileNumber: string) {
        return this.client.post('/api/v1/auth/send-otp', { mobile_number: mobileNumber });
    }

    async verifyOTP(mobileNumber: string, otp: string) {
        return this.client.post('/api/v1/auth/verify-otp', {
            mobile_number: mobileNumber,
            otp,
        });
    }

    async logout() {
        try {
            await this.client.post('/api/v1/auth/logout');
        } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        }
    }

    // Product endpoints
    async getProducts(params?: { skip?: number; limit?: number; category?: string }) {
        return this.client.get('/api/v1/products', { params });
    }

    async getProduct(id: string) {
        return this.client.get(`/api/v1/products/${id}`);
    }

    async getProductBySlug(slug: string) {
        // No dedicated slug endpoint — filter via query params
        const response = await this.client.get('/api/v1/products', { params: { slug } });
        // Return first matching product in the expected shape
        const products = response.data?.items || response.data || [];
        const product = Array.isArray(products) ? products.find((p: any) => p.slug === slug) : null;
        return { data: product || null };
    }

    // Cart endpoints
    async getCart() {
        return this.client.get('/api/v1/cart');
    }

    async addToCart(productId: string, quantity: number) {
        return this.client.post('/api/v1/cart/add', {
            product_id: productId,
            quantity,
        });
    }

    async updateCartItem(itemId: string, quantity: number) {
        return this.client.put(`/api/v1/cart/${itemId}`, { quantity });
    }

    async removeFromCart(itemId: string) {
        return this.client.delete(`/api/v1/cart/${itemId}`);
    }

    async clearCart() {
        return this.client.post('/api/v1/cart/clear');
    }

    // Order endpoints
    async createOrder(addressId: string) {
        return this.client.post('/api/v1/orders', { address_id: addressId });
    }

    async getOrders(params?: { skip?: number; limit?: number }) {
        return this.client.get('/api/v1/orders', { params });
    }

    async getOrder(id: string) {
        return this.client.get(`/api/v1/orders/${id}`);
    }

    async trackOrder(id: string) {
        return this.client.get(`/api/v1/orders/${id}/track`);
    }

    async cancelOrder(id: string) {
        return this.client.post(`/api/v1/orders/${id}/cancel`);
    }

    // Payment endpoints
    async createPayment(orderId: string) {
        return this.client.post('/api/v1/payments/create', { order_id: orderId });
    }

    async verifyPayment(data: {
        razorpay_order_id: string;
        razorpay_payment_id: string;
        razorpay_signature: string;
    }) {
        return this.client.post('/api/v1/payments/verify', data);
    }

    // User endpoints
    async getProfile() {
        return this.client.get('/api/v1/users/me');
    }

    async updateProfile(data: { name?: string; email?: string }) {
        return this.client.put('/api/v1/users/me', data);
    }

    async getAddresses() {
        return this.client.get('/api/v1/users/me/addresses');
    }

    async createAddress(data: {
        name: string;
        mobile: string;
        line1: string;
        line2?: string;
        city: string;
        state: string;
        pincode: string;
        landmark?: string;
        is_default?: boolean;
    }) {
        return this.client.post('/api/v1/users/me/addresses', data);
    }

    async updateAddress(id: string, data: Partial<{
        name: string;
        mobile: string;
        line1: string;
        line2: string;
        city: string;
        state: string;
        pincode: string;
        landmark: string;
        is_default: boolean;
    }>) {
        return this.client.put(`/api/v1/users/me/addresses/${id}`, data);
    }

    async deleteAddress(id: string) {
        return this.client.delete(`/api/v1/users/me/addresses/${id}`);
    }
    async mergeCart(items: { product_id: string; quantity: number }[]) {
        return this.client.post('/api/v1/cart/merge', items);
    }
}

export const apiService = new ApiService();
export default apiService;
