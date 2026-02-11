import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme.dart';
import '../../providers/order_provider.dart';

class OrderDetailScreen extends ConsumerWidget {
  final String orderId;
  
  const OrderDetailScreen({super.key, required this.orderId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orderAsync = ref.watch(orderDetailProvider(orderId));
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Order Details'),
      ),
      body: orderAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('Error: $error')),
        data: (order) {
          if (order == null) {
            return const Center(child: Text('Order not found'));
          }
          
          final status = order['status'] ?? 'pending';
          final steps = ['Confirmed', 'Shipped', 'Out for Delivery', 'Delivered'];
          final currentStep = {
            'pending': -1,
            'confirmed': 0,
            'shipped': 1,
            'out_for_delivery': 2,
            'delivered': 3,
          }[status] ?? -1;
          
          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Status card
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: AppTheme.primaryGradient,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.receipt_long, color: Colors.white),
                          const SizedBox(width: 8),
                          Text(
                            'Order #${order['order_number'] ?? orderId.substring(0, 8)}',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        status.toString().replaceAll('_', ' ').toUpperCase(),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                
                // Timeline
                if (currentStep >= 0) ...[
                  Text(
                    'Order Timeline',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  ...List.generate(steps.length, (index) {
                    final isCompleted = index <= currentStep;
                    final isCurrent = index == currentStep;
                    
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Column(
                          children: [
                            Container(
                              width: 24,
                              height: 24,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: isCompleted ? AppTheme.accentColor : AppTheme.lightBorder,
                              ),
                              child: isCompleted
                                  ? const Icon(Icons.check, color: Colors.white, size: 16)
                                  : null,
                            ),
                            if (index < steps.length - 1)
                              Container(
                                width: 2,
                                height: 40,
                                color: isCompleted ? AppTheme.accentColor : AppTheme.lightBorder,
                              ),
                          ],
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Padding(
                            padding: const EdgeInsets.only(bottom: 24),
                            child: Text(
                              steps[index],
                              style: TextStyle(
                                fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                                color: isCompleted ? AppTheme.lightText : AppTheme.lightTextMuted,
                              ),
                            ),
                          ),
                        ),
                      ],
                    );
                  }),
                  const SizedBox(height: 24),
                ],
                
                // Items
                Text(
                  'Items',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 12),
                ...((order['items'] as List?) ?? []).map((item) {
                  final product = item['product'] ?? {};
                  return Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.lightBorder),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 60,
                          height: 60,
                          decoration: BoxDecoration(
                            color: AppTheme.lightBackground,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(Icons.image, color: AppTheme.lightTextMuted),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                product['name'] ?? 'Product',
                                style: Theme.of(context).textTheme.titleMedium,
                              ),
                              Text(
                                'Qty: ${item['quantity']}',
                                style: TextStyle(color: AppTheme.lightTextMuted),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          '₹${item['price'] ?? product['price'] ?? 0}',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  );
                }),
                const SizedBox(height: 24),
                
                // Total
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.lightBackground,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Subtotal'),
                          Text('₹${order['subtotal'] ?? order['total'] ?? 0}'),
                        ],
                      ),
                      const SizedBox(height: 8),
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Delivery'),
                          Text('FREE', style: TextStyle(color: AppTheme.accentColor)),
                        ],
                      ),
                      const Divider(height: 24),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Total',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          Text(
                            '₹${order['total'] ?? 0}',
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                
                // Delivery Address
                if (order['address'] != null) ...[
                  Text(
                    'Delivery Address',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.lightBorder),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.location_on_outlined, color: AppTheme.primaryColor),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                order['address']['full_name'] ?? '',
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                              Text(
                                '${order['address']['street'] ?? ''}, ${order['address']['city'] ?? ''}, ${order['address']['state'] ?? ''} - ${order['address']['pincode'] ?? ''}',
                                style: TextStyle(color: AppTheme.lightTextMuted),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}
