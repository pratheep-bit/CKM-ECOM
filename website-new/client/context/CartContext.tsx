import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';

export interface Product {
    id: string;
    name: string;
    price: number;
    images: string[];
    slug: string;
    stock: number;
    is_active: boolean;
}

export interface CartItem {
    id?: string; // Optional for guest items
    product_id: string;
    quantity: number;
    product: Product;
}

interface CartContextType {
    items: CartItem[];
    itemCount: number;
    subtotal: number;
    loading: boolean;
    addToCart: (product: Product, quantity?: number) => Promise<void>;
    removeFromCart: (productId: string) => Promise<void>;
    updateQuantity: (productId: string, quantity: number) => Promise<void>;
    clearCart: () => Promise<void>;
    refreshCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
    const [items, setItems] = useState<CartItem[]>([]);
    const [loading, setLoading] = useState(true);
    const { isLoggedIn } = useAuth();

    // Calculate totals
    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
    const subtotal = items.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);

    // Initial load + refresh on auth change
    useEffect(() => {
        refreshCart();
    }, [isLoggedIn]);

    const refreshCart = async () => {
        setLoading(true);
        try {
            if (isLoggedIn) {
                // Merge guest cart items first (if any)
                const guestCartStr = localStorage.getItem('guest_cart');
                if (guestCartStr) {
                    try {
                        const guestItems: CartItem[] = JSON.parse(guestCartStr);
                        if (guestItems.length > 0) {
                            const mergePayload = guestItems.map(item => ({
                                product_id: item.product_id,
                                quantity: item.quantity
                            }));
                            await apiService.mergeCart(mergePayload);
                        }
                    } catch (err) {
                        console.error("Failed to merge cart:", err);
                    } finally {
                        // Always remove guest cart after merge attempt
                        localStorage.removeItem('guest_cart');
                    }
                }

                // Fetch server-side cart (loading still true)
                const response = await apiService.getCart();
                const cartItems = response.data?.items || [];
                setItems(cartItems);
            } else {
                // Guest mode: read from localStorage
                const saved = localStorage.getItem('guest_cart');
                if (saved) {
                    try {
                        setItems(JSON.parse(saved));
                    } catch {
                        setItems([]);
                        localStorage.removeItem('guest_cart');
                    }
                } else {
                    setItems([]);
                }
            }
        } catch (error) {
            console.error('Failed to load cart:', error);
            if (!isLoggedIn) setItems([]);
        } finally {
            setLoading(false);
        }
    };

    const addToCart = async (product: Product, quantity = 1) => {
        if (!product.is_active || product.stock < quantity) {
            toast.error('Product not available or out of stock');
            return;
        }

        try {
            if (isLoggedIn) {
                await apiService.addToCart(product.id, quantity);
                await refreshCart();
                toast.success('Added to cart');
            } else {
                // Guest Logic
                const currentItems = [...items];
                const existingIndex = currentItems.findIndex(i => i.product_id === product.id);

                if (existingIndex >= 0) {
                    const newQty = currentItems[existingIndex].quantity + quantity;
                    if (newQty > product.stock) {
                        toast.error(`Only ${product.stock} items available`);
                        return;
                    }
                    currentItems[existingIndex].quantity = Math.min(newQty, 10);
                } else {
                    currentItems.push({
                        product_id: product.id,
                        quantity: Math.min(quantity, 10),
                        product: product
                    });
                }

                setItems(currentItems);
                localStorage.setItem('guest_cart', JSON.stringify(currentItems));
                toast.success('Added to cart');
            }
        } catch (error) {
            console.error('Add to cart error:', error);
            toast.error('Failed to add to cart');
        }
    };

    const updateQuantity = async (productId: string, quantity: number) => {
        if (quantity < 1) return;

        try {
            if (isLoggedIn) {
                const item = items.find(i => i.product_id === productId);
                if (item?.id) {
                    await apiService.updateCartItem(item.id, quantity);
                    await refreshCart();
                }
            } else {
                const currentItems = [...items];
                const index = currentItems.findIndex(i => i.product_id === productId);
                if (index >= 0) {
                    if (currentItems[index].product.stock < quantity) {
                        toast.error(`Only ${currentItems[index].product.stock} items available`);
                        return;
                    }
                    currentItems[index].quantity = quantity;
                    setItems(currentItems);
                    localStorage.setItem('guest_cart', JSON.stringify(currentItems));
                }
            }
        } catch (error) {
            console.error('Update quantity error:', error);
            toast.error('Failed to update quantity');
        }
    };

    const removeFromCart = async (productId: string) => {
        try {
            if (isLoggedIn) {
                const item = items.find(i => i.product_id === productId);
                if (item?.id) {
                    await apiService.removeFromCart(item.id);
                    await refreshCart();
                    toast.success('Removed from cart');
                }
            } else {
                const newItems = items.filter(i => i.product_id !== productId);
                setItems(newItems);
                localStorage.setItem('guest_cart', JSON.stringify(newItems));
                toast.success('Removed from cart');
            }
        } catch (error) {
            console.error('Remove error:', error);
            toast.error('Failed to remove item');
        }
    };

    const clearCart = async () => {
        try {
            if (isLoggedIn) {
                await apiService.clearCart();
            }
        } catch (error) {
            console.error('Clear cart error:', error);
        } finally {
            setItems([]);
            localStorage.removeItem('guest_cart');
        }
    };

    return (
        <CartContext.Provider value={{
            items,
            itemCount,
            subtotal,
            loading,
            addToCart,
            removeFromCart,
            updateQuantity,
            clearCart,
            refreshCart
        }}>
            {children}
        </CartContext.Provider>
    );
}

export function useCart() {
    const context = useContext(CartContext);
    if (context === undefined) {
        throw new Error('useCart must be used within a CartProvider');
    }
    return context;
}
