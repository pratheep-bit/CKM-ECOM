import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/theme.dart';
import '../../providers/product_provider.dart';
import '../../providers/cart_provider.dart';

class ProductScreen extends ConsumerWidget {
  final String productId;
  
  const ProductScreen({super.key, required this.productId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productAsync = ref.watch(productProvider(productId));
    
    return Scaffold(
      body: productAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('Error: $error')),
        data: (product) {
          if (product == null) {
            return const Center(child: Text('Product not found'));
          }
          
          return CustomScrollView(
            slivers: [
              // App Bar with image
              SliverAppBar(
                expandedHeight: 400,
                pinned: true,
                flexibleSpace: FlexibleSpaceBar(
                  background: Container(
                    color: AppTheme.lightBackground,
                    child: product['image_url'] != null
                        ? CachedNetworkImage(
                            imageUrl: product['image_url'],
                            fit: BoxFit.cover,
                          )
                        : const Center(
                            child: Icon(
                              Icons.image,
                              size: 80,
                              color: AppTheme.lightTextMuted,
                            ),
                          ),
                  ),
                ),
              ),
              
              // Product details
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Badge
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: const Text(
                          'Best Seller',
                          style: TextStyle(
                            color: AppTheme.primaryColor,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      // Name
                      Text(
                        product['name'] ?? 'Premium Product',
                        style: Theme.of(context).textTheme.displaySmall,
                      ),
                      const SizedBox(height: 8),
                      
                      // Rating
                      Row(
                        children: [
                          ...List.generate(5, (index) => const Icon(
                            Icons.star,
                            size: 20,
                            color: AppTheme.warningColor,
                          )),
                          const SizedBox(width: 8),
                          Text(
                            '4.9 (1,247 reviews)',
                            style: TextStyle(color: AppTheme.lightTextMuted),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      
                      // Price
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: AppTheme.lightBackground,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Row(
                          children: [
                            Text(
                              '₹${product['price'] ?? '14,999'}',
                              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 12),
                            if (product['original_price'] != null)
                              Text(
                                '₹${product['original_price']}',
                                style: TextStyle(
                                  color: AppTheme.lightTextMuted,
                                  decoration: TextDecoration.lineThrough,
                                  fontSize: 18,
                                ),
                              ),
                            const Spacer(),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 6,
                              ),
                              decoration: BoxDecoration(
                                color: AppTheme.accentColor.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text(
                                '25% OFF',
                                style: TextStyle(
                                  color: AppTheme.accentColor,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),
                      
                      // Description
                      Text(
                        'Description',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        product['description'] ?? 'Experience unparalleled quality with our flagship product. Crafted with precision using premium materials, this product delivers exceptional performance and lasting durability.',
                        style: TextStyle(
                          color: AppTheme.lightTextMuted,
                          height: 1.6,
                        ),
                      ),
                      const SizedBox(height: 24),
                      
                      // Features
                      Text(
                        'Features',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 12),
                      ...['Premium quality materials', 'Ergonomic design', 'Advanced technology', '2-year warranty', 'Free delivery'].map(
                        (feature) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.check_circle,
                                color: AppTheme.accentColor,
                                size: 20,
                              ),
                              const SizedBox(width: 12),
                              Text(feature),
                            ],
                          ),
                        ),
                      ),
                      
                      // Spacing
                      const SizedBox(height: 100),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border(
            top: BorderSide(color: AppTheme.lightBorder),
          ),
        ),
        child: SafeArea(
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () {
                    ref.read(cartProvider.notifier).addItem(productId, 1);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Added to cart')),
                    );
                  },
                  child: const Text('Add to Cart'),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    ref.read(cartProvider.notifier).addItem(productId, 1);
                    context.push('/checkout');
                  },
                  child: const Text('Buy Now'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
