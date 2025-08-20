// lib/features/auth/screens/otp_screen.dart

import 'dart:async';
import 'package:fatura_yeni/core/services/api_service.dart';
import 'package:fatura_yeni/core/services/firebase_service.dart';
import 'package:fatura_yeni/core/services/storage_service.dart';
import 'package:flutter/material.dart';
import 'package:pinput/pinput.dart';
import 'package:fatura_yeni/features/main/main_screen.dart';

class OtpScreen extends StatefulWidget {
  final String verificationId;
  final String name;
  final String email;
  final String password;
  final String fullPhoneNumber;

  const OtpScreen({
    super.key,
    required this.verificationId,
    required this.name,
    required this.email,
    required this.password,
    required this.fullPhoneNumber,
  });

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final TextEditingController _pinController = TextEditingController();
  final FirebaseService _firebaseService = FirebaseService();
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();
  bool _isLoading = false;

  late Timer _timer;
  int _start = 120; // 2 dakika

  @override
  void initState() {
    super.initState();
    startTimer();
  }

  void startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_start == 0) {
        setState(() {
          timer.cancel();
        });
      } else {
        setState(() {
          _start--;
        });
      }
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    _pinController.dispose();
    super.dispose();
  }

  Future<void> _verifyAndRegister() async {
    if (_pinController.text.length != 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lütfen 6 haneli kodu girin.')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final firebaseIdToken =
          await _firebaseService.getFirebaseIdTokenWithSmsCode(
        widget.verificationId,
        _pinController.text,
      );

      if (firebaseIdToken == null) {
        throw Exception("Firebase ID token alınamadı.");
      }

      final response = await _apiService.register(
        email: widget.email,
        password: widget.password,
        phone: widget.fullPhoneNumber, // 'name' yerine 'phone' gönder
        firebaseIdToken: firebaseIdToken,
      );

      await _storageService.saveToken(response['token']);

      if (mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (context) => const MainScreen()),
          (Route<dynamic> route) => false,
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Kayıt başarısız: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  String get timerString {
    int minutes = _start ~/ 60;
    int seconds = _start % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final screenSize = MediaQuery.of(context).size;

    return Scaffold(
      appBar: AppBar(
        leading: const BackButton(),
        title: Text(
          "OTP Verification",
          style:
              theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: screenSize.width * 0.08),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(flex: 1),
              _buildHeaderTexts(context),
              const SizedBox(height: 32),
              _buildOtpInput(context),
              const SizedBox(height: 24),
              _buildResendCode(context),
              const Spacer(flex: 2),
              ElevatedButton(
                onPressed: _isLoading ? null : _verifyAndRegister,
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Verify and Create Account'),
              ),
              const Spacer(flex: 1),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeaderTexts(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "Please Enter\nOTP Verification",
          style: theme.textTheme.displayLarge?.copyWith(fontSize: 28),
        ),
        const SizedBox(height: 16),
        RichText(
          text: TextSpan(
            style: theme.textTheme.bodyLarge?.copyWith(color: Colors.grey[600]),
            children: [
              TextSpan(text: "Code was sent to ${widget.fullPhoneNumber}\n"),
              const TextSpan(text: "This code will expire in "),
              TextSpan(
                text: timerString,
                style: const TextStyle(color: Colors.redAccent),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildOtpInput(BuildContext context) {
    final defaultPinTheme = PinTheme(
      width: 60,
      height: 60,
      textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(8),
      ),
    );

    return Pinput(
      length: 6, // Firebase 6 haneli kod gönderir
      controller: _pinController,
      defaultPinTheme: defaultPinTheme,
      focusedPinTheme: defaultPinTheme.copyWith(
        decoration: defaultPinTheme.decoration!.copyWith(
          border: Border.all(color: Theme.of(context).primaryColor),
        ),
      ),
      onCompleted: (pin) {
        _verifyAndRegister();
      },
    );
  }

  Widget _buildResendCode(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          "Didn't receive an OTP?",
          style: theme.textTheme.bodyLarge?.copyWith(color: Colors.grey[600]),
        ),
        TextButton(
          onPressed: _start == 0
              ? () async {
                  // Resend OTP logic
                  await _firebaseService.resendOtp(widget.fullPhoneNumber);
                  setState(() {
                    _start = 120;
                  });
                  startTimer();
                }
              : null, // Disable button if timer is running
          child: Text(
            "Resend",
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: _start == 0 ? theme.primaryColor : Colors.grey,
            ),
          ),
        )
      ],
    );
  }
}
