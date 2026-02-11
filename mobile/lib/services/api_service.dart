import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl = 'https://api.yourstore.com/api/v1';
  
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));
    
    // Add interceptor for auth token
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Try to refresh token
          final refreshed = await _refreshToken();
          if (refreshed) {
            // Retry original request
            final opts = error.requestOptions;
            final token = await _storage.read(key: 'access_token');
            opts.headers['Authorization'] = 'Bearer $token';
            final response = await _dio.fetch(opts);
            return handler.resolve(response);
          }
        }
        return handler.next(error);
      },
    ));
  }
  
  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken == null) return false;
      
      final response = await Dio().post(
        '$baseUrl/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      
      await _storage.write(key: 'access_token', value: response.data['access_token']);
      await _storage.write(key: 'refresh_token', value: response.data['refresh_token']);
      
      return true;
    } catch (e) {
      return false;
    }
  }
  
  // Auth
  Future<Response> sendOtp(String mobile) async {
    return _dio.post('/auth/send-otp', data: {'mobile_number': mobile});
  }
  
  Future<Response> verifyOtp(String mobile, String otp) async {
    return _dio.post('/auth/verify-otp', data: {
      'mobile_number': mobile,
      'otp': otp,
    });
  }
  
  // Products
  Future<Response> getProducts({int page = 1, int pageSize = 10}) async {
    return _dio.get('/products', queryParameters: {
      'page': page,
      'page_size': pageSize,
    });
  }
  
  Future<Response> getProduct(String id) async {
    return _dio.get('/products/$id');
  }
  
  // Cart
  Future<Response> getCart() async {
    return _dio.get('/cart');
  }
  
  Future<Response> addToCart(String productId, int quantity) async {
    return _dio.post('/cart/add', data: {
      'product_id': productId,
      'quantity': quantity,
    });
  }
  
  Future<Response> updateCartItem(String itemId, int quantity) async {
    return _dio.put('/cart/$itemId', data: {'quantity': quantity});
  }
  
  Future<Response> removeFromCart(String itemId) async {
    return _dio.delete('/cart/$itemId');
  }
  
  // Addresses
  Future<Response> getAddresses() async {
    return _dio.get('/users/me/addresses');
  }
  
  Future<Response> addAddress(Map<String, dynamic> address) async {
    return _dio.post('/users/me/addresses', data: address);
  }
  
  // Orders
  Future<Response> createOrder(String addressId) async {
    return _dio.post('/orders', data: {'address_id': addressId});
  }
  
  Future<Response> getOrders({int page = 1}) async {
    return _dio.get('/orders', queryParameters: {'page': page});
  }
  
  Future<Response> getOrder(String id) async {
    return _dio.get('/orders/$id');
  }
  
  Future<Response> trackOrder(String id) async {
    return _dio.get('/orders/$id/track');
  }
  
  // Payments
  Future<Response> createPayment(String orderId) async {
    return _dio.post('/payments/create', data: {'order_id': orderId});
  }
  
  Future<Response> verifyPayment({
    required String razorpayOrderId,
    required String razorpayPaymentId,
    required String razorpaySignature,
  }) async {
    return _dio.post('/payments/verify', data: {
      'razorpay_order_id': razorpayOrderId,
      'razorpay_payment_id': razorpayPaymentId,
      'razorpay_signature': razorpaySignature,
    });
  }
  
  // User
  Future<Response> getProfile() async {
    return _dio.get('/users/me');
  }
  
  Future<Response> updateProfile(Map<String, dynamic> data) async {
    return _dio.put('/users/me', data: data);
  }

  // Logout
  Future<Response> logout() async {
    return _dio.post('/auth/logout');
  }
}

// Singleton instance
final apiService = ApiService();
