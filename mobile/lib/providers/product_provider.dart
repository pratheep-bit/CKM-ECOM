import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

// Products provider
final productsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  try {
    final response = await apiService.getProducts();
    final items = response.data['items'] as List? ?? [];
    return items.map((e) => e as Map<String, dynamic>).toList();
  } catch (e) {
    return [];
  }
});

// Single product provider
final productProvider = FutureProvider.family<Map<String, dynamic>?, String>((ref, id) async {
  try {
    final response = await apiService.getProduct(id);
    return response.data as Map<String, dynamic>;
  } catch (e) {
    return null;
  }
});
