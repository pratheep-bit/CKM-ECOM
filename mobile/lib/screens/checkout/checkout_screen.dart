import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../providers/cart_provider.dart';
import '../../providers/order_provider.dart';

class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  int _currentStep = 0;
  String? _selectedAddressId;
  bool _isProcessing = false;
  
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();
  final _cityController = TextEditingController();
  final _stateController = TextEditingController();
  final _pincodeController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    _cityController.dispose();
    _stateController.dispose();
    _pincodeController.dispose();
    super.dispose();
  }

  Future<void> _placeOrder() async {
    if (_selectedAddressId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a delivery address')),
      );
      return;
    }
    
    setState(() => _isProcessing = true);
    
    try {
      final order = await ref.read(orderProvider.notifier).createOrder(_selectedAddressId!);
      
      if (mounted && order != null) {
        // Process payment
        await ref.read(orderProvider.notifier).processPayment(order['id']);
        
        // Navigate to success
        context.go('/orders/${order['id']}');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Order failed: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => _isProcessing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final cartState = ref.watch(cartProvider);
    final cart = cartState.cart;
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Checkout'),
      ),
      body: Column(
        children: [
          Expanded(
            child: Stepper(
              currentStep: _currentStep,
              onStepContinue: () {
                if (_currentStep < 2) {
                  setState(() => _currentStep++);
                } else {
                  _placeOrder();
                }
              },
              onStepCancel: () {
                if (_currentStep > 0) {
                  setState(() => _currentStep--);
                }
              },
              steps: [
                // Delivery Address
                Step(
                  title: const Text('Delivery Address'),
                  content: Column(
                    children: [
                      TextField(
                        controller: _nameController,
                        decoration: const InputDecoration(
                          labelText: 'Full Name',
                          hintText: 'Enter your full name',
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        decoration: const InputDecoration(
                          labelText: 'Phone Number',
                          hintText: '9876543210',
                          prefixText: '+91 ',
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _addressController,
                        maxLines: 2,
                        decoration: const InputDecoration(
                          labelText: 'Address',
                          hintText: 'House no, Building, Street, Area',
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _cityController,
                              decoration: const InputDecoration(
                                labelText: 'City',
                              ),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: TextField(
                              controller: _stateController,
                              decoration: const InputDecoration(
                                labelText: 'State',
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _pincodeController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'PIN Code',
                          hintText: '600001',
                        ),
                      ),
                    ],
                  ),
                  isActive: _currentStep >= 0,
                ),
                
                // Order Summary
                Step(
                  title: const Text('Order Summary'),
                  content: Column(
                    children: [
                      ...((cart['items'] as List?) ?? []).map((item) {
                        final product = item['product'] ?? {};
                        return ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: Container(
                            width: 50,
                            height: 50,
                            decoration: BoxDecoration(
                              color: AppTheme.lightBackground,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Icon(Icons.image),
                          ),
                          title: Text(product['name'] ?? 'Product'),
                          subtitle: Text('Qty: ${item['quantity']}'),
                          trailing: Text('₹${product['price'] ?? 0}'),
                        );
                      }),
                      const Divider(),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Subtotal'),
                        trailing: Text('₹${cart['subtotal'] ?? cart['total'] ?? 0}'),
                      ),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Delivery'),
                        trailing: const Text('FREE', style: TextStyle(color: AppTheme.accentColor)),
                      ),
                      const Divider(),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text(
                          'Total',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        trailing: Text(
                          '₹${cart['total'] ?? 0}',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  isActive: _currentStep >= 1,
                ),
                
                // Payment
                Step(
                  title: const Text('Payment'),
                  content: Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          border: Border.all(color: AppTheme.primaryColor, width: 2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 48,
                              height: 48,
                              decoration: BoxDecoration(
                                color: AppTheme.primaryColor.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Icon(
                                Icons.payment,
                                color: AppTheme.primaryColor,
                              ),
                            ),
                            const SizedBox(width: 16),
                            const Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Razorpay',
                                    style: TextStyle(fontWeight: FontWeight.bold),
                                  ),
                                  Text('UPI, Cards, Netbanking, Wallets'),
                                ],
                              ),
                            ),
                            const Icon(
                              Icons.check_circle,
                              color: AppTheme.primaryColor,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'You will be redirected to Razorpay payment gateway',
                        style: TextStyle(color: AppTheme.lightTextMuted),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                  isActive: _currentStep >= 2,
                ),
              ],
            ),
          ),
          
          // Place Order Button
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border(
                top: BorderSide(color: AppTheme.lightBorder),
              ),
            ),
            child: SafeArea(
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Total'),
                      Text(
                        '₹${cart['total'] ?? 0}',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _isProcessing ? null : _placeOrder,
                      child: _isProcessing
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Text('Place Order'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
