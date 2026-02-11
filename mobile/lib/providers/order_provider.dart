import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:razorpay_flutter/razorpay_flutter.dart';
import '../services/api_service.dart';

// Order state
class OrderState {
  final List<Map<String, dynamic>> orders;
  final bool isLoading;
  final String? error;
  
  const OrderState({
    this.orders = const [],
    this.isLoading = false,
    this.error,
  });
  
  OrderState copyWith({
    List<Map<String, dynamic>>? orders,
    bool? isLoading,
    String? error,
  }) {
    return OrderState(
      orders: orders ?? this.orders,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

// Order notifier
class OrderNotifier extends StateNotifier<OrderState> {
  Razorpay? _razorpay;
  
  OrderNotifier() : super(const OrderState()) {
    loadOrders();
    _initRazorpay();
  }
  
  void _initRazorpay() {
    _razorpay = Razorpay();
    _razorpay!.on(Razorpay.EVENT_PAYMENT_SUCCESS, _handlePaymentSuccess);
    _razorpay!.on(Razorpay.EVENT_PAYMENT_ERROR, _handlePaymentError);
  }
  
  void _handlePaymentSuccess(PaymentSuccessResponse response) async {
    try {
      await apiService.verifyPayment(
        razorpayOrderId: response.orderId!,
        razorpayPaymentId: response.paymentId!,
        razorpaySignature: response.signature!,
      );
      await loadOrders();
    } catch (e) {
      // Handle error
    }
  }
  
  void _handlePaymentError(PaymentFailureResponse response) {
    // Handle payment failure
  }
  
  Future<void> loadOrders() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await apiService.getOrders();
      final items = response.data['items'] as List? ?? [];
      state = state.copyWith(
        orders: items.map((e) => e as Map<String, dynamic>).toList(),
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load orders',
      );
    }
  }
  
  Future<Map<String, dynamic>?> createOrder(String addressId) async {
    try {
      final response = await apiService.createOrder(addressId);
      await loadOrders();
      return response.data as Map<String, dynamic>;
    } catch (e) {
      return null;
    }
  }
  
  Future<void> processPayment(String orderId) async {
    try {
      final response = await apiService.createPayment(orderId);
      final data = response.data;
      
      var options = {
        'key': data['razorpay_key'],
        'order_id': data['razorpay_order_id'],
        'amount': data['amount'],
        'name': 'Brand Store',
        'description': 'Order Payment',
        'prefill': {
          'contact': data['mobile'] ?? '',
          'email': data['email'] ?? '',
        },
      };
      
      _razorpay!.open(options);
    } catch (e) {
      rethrow;
    }
  }
  
  @override
  void dispose() {
    _razorpay?.clear();
    super.dispose();
  }
}

// Provider
final orderProvider = StateNotifierProvider<OrderNotifier, OrderState>((ref) {
  return OrderNotifier();
});

// Single order provider
final orderDetailProvider = FutureProvider.family<Map<String, dynamic>?, String>((ref, id) async {
  try {
    final response = await apiService.getOrder(id);
    return response.data as Map<String, dynamic>;
  } catch (e) {
    return null;
  }
});
