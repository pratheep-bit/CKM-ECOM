import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../lib/api';

// Product hooks
export const useProducts = (params?: { skip?: number; limit?: number; category?: string }) => {
    return useQuery({
        queryKey: ['products', params],
        queryFn: () => apiService.getProducts(params),
    });
};

export const useProduct = (id: string) => {
    return useQuery({
        queryKey: ['product', id],
        queryFn: () => apiService.getProduct(id),
        enabled: !!id,
    });
};

export const useProductBySlug = (slug: string) => {
    return useQuery({
        queryKey: ['product', 'slug', slug],
        queryFn: () => apiService.getProductBySlug(slug),
        enabled: !!slug,
    });
};

// Cart hooks
export const useCart = () => {
    return useQuery({
        queryKey: ['cart'],
        queryFn: () => apiService.getCart(),
    });
};

export const useAddToCart = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
            apiService.addToCart(productId, quantity),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cart'] });
        },
    });
};

export const useUpdateCartItem = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ itemId, quantity }: { itemId: string; quantity: number }) =>
            apiService.updateCartItem(itemId, quantity),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cart'] });
        },
    });
};

export const useRemoveFromCart = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (itemId: string) => apiService.removeFromCart(itemId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cart'] });
        },
    });
};

export const useClearCart = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => apiService.clearCart(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cart'] });
        },
    });
};

// Order hooks
export const useOrders = (params?: { skip?: number; limit?: number }) => {
    const token = localStorage.getItem('access_token');
    return useQuery({
        queryKey: ['orders', params],
        queryFn: () => apiService.getOrders(params),
        enabled: !!token,
    });
};

export const useOrder = (id: string) => {
    return useQuery({
        queryKey: ['order', id],
        queryFn: () => apiService.getOrder(id),
        enabled: !!id,
    });
};

export const useCreateOrder = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (addressId: string) => apiService.createOrder(addressId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['orders'] });
            queryClient.invalidateQueries({ queryKey: ['cart'] });
        },
    });
};

// User hooks
export const useProfile = () => {
    const token = localStorage.getItem('access_token');
    return useQuery({
        queryKey: ['profile'],
        queryFn: () => apiService.getProfile(),
        enabled: !!token,
    });
};

export const useUpdateProfile = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: { name?: string; email?: string }) =>
            apiService.updateProfile(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['profile'] });
        },
    });
};

export const useAddresses = () => {
    const token = localStorage.getItem('access_token');
    return useQuery({
        queryKey: ['addresses'],
        queryFn: () => apiService.getAddresses(),
        enabled: !!token,
    });
};

export const useCreateAddress = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: {
            name: string;
            mobile: string;
            line1: string;
            line2?: string;
            city: string;
            state: string;
            pincode: string;
            landmark?: string;
            is_default?: boolean;
        }) => apiService.createAddress(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['addresses'] });
        },
    });
};

// Auth hooks
export const useSendOTP = () => {
    return useMutation({
        mutationFn: (mobileNumber: string) => apiService.sendOTP(mobileNumber),
    });
};

export const useVerifyOTP = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ mobileNumber, otp }: { mobileNumber: string; otp: string }) =>
            apiService.verifyOTP(mobileNumber, otp),
        onSuccess: () => {
            // Token storage is handled by AuthContext.login()
            queryClient.invalidateQueries({ queryKey: ['profile'] });
        },
    });
};

export const useLogout = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => apiService.logout(),
        onSuccess: () => {
            queryClient.clear();
        },
    });
};

export const useCancelOrder = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (orderId: string) => apiService.cancelOrder(orderId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['orders'] });
        },
    });
};
