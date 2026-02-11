import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../services/api_service.dart';

// Auth state
class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final String? error;
  final Map<String, dynamic>? user;
  
  const AuthState({
    this.isAuthenticated = false,
    this.isLoading = false,
    this.error,
    this.user,
  });
  
  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    String? error,
    Map<String, dynamic>? user,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      user: user ?? this.user,
    );
  }
}

// Auth notifier
class AuthNotifier extends StateNotifier<AuthState> {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  AuthNotifier() : super(const AuthState()) {
    _checkAuth();
  }
  
  Future<void> _checkAuth() async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      state = state.copyWith(isAuthenticated: true);
      await loadProfile();
    }
  }
  
  Future<void> sendOtp(String mobile) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await apiService.sendOtp(mobile);
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to send OTP. Please try again.',
      );
      rethrow;
    }
  }
  
  Future<bool> verifyOtp(String mobile, String otp) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await apiService.verifyOtp(mobile, otp);
      final data = response.data;
      
      await _storage.write(key: 'access_token', value: data['access_token']);
      await _storage.write(key: 'refresh_token', value: data['refresh_token']);
      
      state = state.copyWith(
        isAuthenticated: true,
        isLoading: false,
      );
      
      await loadProfile();
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Invalid OTP. Please try again.',
      );
      return false;
    }
  }
  
  Future<void> loadProfile() async {
    try {
      final response = await apiService.getProfile();
      state = state.copyWith(user: response.data);
    } catch (e) {
      // Ignore profile load errors
    }
  }
  
  Future<void> logout() async {
    try {
      await apiService.logout();
    } catch (e) {
      // Ignore network errors on logout, still clear local storage
    }
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
    state = const AuthState();
  }
}

// Providers
final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});
