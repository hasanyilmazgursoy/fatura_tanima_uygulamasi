// lib/features/auth/screens/otp_screen.dart

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:pinput/pinput.dart';
import 'package:fatura_yeni/features/main/main_screen.dart';

class OtpScreen extends StatefulWidget {
  const OtpScreen({super.key});

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  late Timer _timer;
  int _start = 228; // 03:48'e denk gelen saniye

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
    super.dispose();
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
                onPressed: () {
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(builder: (context) => const MainScreen()),
                    (Route<dynamic> route) =>
                        false, // Geriye kalan tüm rotaları kaldır
                  );
                },
                child: const Text('Verify and Create Account'),
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
              const TextSpan(text: "Code was sent to +234 7085 689 ***\n"),
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
      length: 4,
      defaultPinTheme: defaultPinTheme,
      focusedPinTheme: defaultPinTheme.copyWith(
        decoration: defaultPinTheme.decoration!.copyWith(
          border: Border.all(color: Theme.of(context).primaryColor),
        ),
      ),
      onCompleted: (pin) {
        // TODO: Handle completed PIN
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
              ? () {
                  // TODO: Resend OTP logic
                  setState(() {
                    _start = 228;
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
