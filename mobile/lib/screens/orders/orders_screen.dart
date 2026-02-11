import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../providers/order_provider.dart';

class OrdersScreen extends ConsumerWidget {
  const OrdersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orderState = ref.watch(orderProvider);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Orders'),
      ),
      body: orderState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : orderState.orders.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.receipt_long_outlined,
                        size: 80,
                        color: AppTheme.lightTextMuted,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'No orders yet',
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Start shopping to see your orders here',
                        style: TextStyle(color: AppTheme.lightTextMuted),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: () => context.go('/'),
                        child: const Text('Start Shopping'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () => ref.read(orderProvider.notifier).loadOrders(),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: orderState.orders.length,
                    itemBuilder: (context, index) {
                      final order = orderState.orders[index];
                      return _OrderCard(order: order);
                    },
                  ),
                ),
    );
  }
}

class _OrderCard extends StatelessWidget {
  final Map<String, dynamic> order;
  
  const _OrderCard({required this.order});

  @override
  Widget build(BuildContext context) {
    final status = order['status'] ?? 'pending';
    final statusColors = {
      'pending': AppTheme.warningColor,
      'confirmed': AppTheme.primaryColor,
      'shipped': AppTheme.secondaryColor,
      'delivered': AppTheme.accentColor,
      'cancelled': AppTheme.errorColor,
    };
    
    return GestureDetector(
      onTap: () => context.push('/orders/${order['id']}'),
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.lightBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Order #${order['order_number'] ?? order['id']?.toString().substring(0, 8)}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: (statusColors[status] ?? AppTheme.lightTextMuted).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    status.toString().toUpperCase(),
                    style: TextStyle(
                      color: statusColors[status] ?? AppTheme.lightTextMuted,
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            
            // Date
            Row(
              children: [
                Icon(Icons.calendar_today_outlined, size: 16, color: AppTheme.lightTextMuted),
                const SizedBox(width: 8),
                Text(
                  order['created_at'] ?? 'Recently ordered',
                  style: TextStyle(color: AppTheme.lightTextMuted),
                ),
              ],
            ),
            const SizedBox(height: 12),
            
            // Items count
            Text(
              '${(order['items'] as List?)?.length ?? 0} item(s)',
              style: TextStyle(color: AppTheme.lightTextMuted),
            ),
            
            const Divider(height: 24),
            
            // Total and action
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Total',
                      style: TextStyle(color: AppTheme.lightTextMuted, fontSize: 12),
                    ),
                    Text(
                      '₹${order['total'] ?? 0}',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                OutlinedButton.icon(
                  onPressed: () => context.push('/orders/${order['id']}'),
                  icon: const Icon(Icons.visibility_outlined, size: 18),
                  label: const Text('View Details'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
