import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:pinput/pinput.dart';
import '../../providers/auth_provider.dart';
import '../../core/theme.dart';

class OtpScreen extends ConsumerStatefulWidget {
  final String mobileNumber;
  
  const OtpScreen({super.key, required this.mobileNumber});

  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  final _otpController = TextEditingController();
  bool _isLoading = false;
  int _resendSeconds = 30;
  bool _canResend = false;

  @override
  void initState() {
    super.initState();
    _startResendTimer();
  }

  void _startResendTimer() {
    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 1));
      if (!mounted) return false;
      setState(() {
        if (_resendSeconds > 0) {
          _resendSeconds--;
        } else {
          _canResend = true;
        }
      });
      return _resendSeconds > 0;
    });
  }

  Future<void> _verifyOtp() async {
    if (_otpController.text.length != 6) return;
    
    setState(() => _isLoading = true);
    
    try {
      final success = await ref.read(authStateProvider.notifier).verifyOtp(
        widget.mobileNumber,
        _otpController.text,
      );
      
      if (mounted && success) {
        context.go('/');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Invalid OTP. Please try again.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _resendOtp() async {
    if (!_canResend) return;
    
    setState(() {
      _canResend = false;
      _resendSeconds = 30;
    });
    
    try {
      await ref.read(authStateProvider.notifier).sendOtp(widget.mobileNumber);
      _startResendTimer();
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('OTP sent successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _canResend = true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to resend OTP')),
        );
      }
    }
  }

  @override
  void dispose() {
    _otpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final defaultPinTheme = PinTheme(
      width: 56,
      height: 56,
      textStyle: Theme.of(context).textTheme.headlineMedium,
      decoration: BoxDecoration(
        border: Border.all(color: AppTheme.lightBorder),
        borderRadius: BorderRadius.circular(12),
      ),
    );
    
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Verify OTP',
                style: Theme.of(context).textTheme.displaySmall,
              ),
              const SizedBox(height: 8),
              Text(
                'Enter the 6-digit code sent to ${widget.mobileNumber}',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: AppTheme.lightTextMuted,
                ),
              ),
              const SizedBox(height: 48),
              
              // OTP Input
              Center(
                child: Pinput(
                  controller: _otpController,
                  length: 6,
                  defaultPinTheme: defaultPinTheme,
                  focusedPinTheme: defaultPinTheme.copyWith(
                    decoration: BoxDecoration(
                      border: Border.all(color: AppTheme.primaryColor, width: 2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  onCompleted: (_) => _verifyOtp(),
                ),
              ),
              const SizedBox(height: 32),
              
              // Verify button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _verifyOtp,
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Verify'),
                ),
              ),
              const SizedBox(height: 24),
              
              // Resend
              Center(
                child: TextButton(
                  onPressed: _canResend ? _resendOtp : null,
                  child: Text(
                    _canResend
                        ? 'Resend OTP'
                        : 'Resend in ${_resendSeconds}s',
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
