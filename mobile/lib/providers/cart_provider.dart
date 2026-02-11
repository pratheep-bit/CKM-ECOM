import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

// Cart state
class CartState {
  final Map<String, dynamic> cart;
  final bool isLoading;
  final String? error;
  
  const CartState({
    this.cart = const {},
    this.isLoading = false,
    this.error,
  });
  
  CartState copyWith({
    Map<String, dynamic>? cart,
    bool? isLoading,
    String? error,
  }) {
    return CartState(
      cart: cart ?? this.cart,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

// Cart notifier
class CartNotifier extends StateNotifier<CartState> {
  CartNotifier() : super(const CartState()) {
    loadCart();
  }
  
  Future<void> loadCart() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await apiService.getCart();
      state = state.copyWith(
        cart: response.data as Map<String, dynamic>,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load cart',
      );
    }
  }
  
  Future<void> addItem(String productId, int quantity) async {
    try {
      await apiService.addToCart(productId, quantity);
      await loadCart();
    } catch (e) {
      // Handle error
    }
  }
  
  Future<void> updateQuantity(String itemId, int quantity) async {
    try {
      await apiService.updateCartItem(itemId, quantity);
      await loadCart();
    } catch (e) {
      // Handle error
    }
  }
  
  Future<void> removeItem(String itemId) async {
    try {
      await apiService.removeFromCart(itemId);
      await loadCart();
    } catch (e) {
      // Handle error
    }
  }
}

// Provider
final cartProvider = StateNotifierProvider<CartNotifier, CartState>((ref) {
  return CartNotifier();
});
