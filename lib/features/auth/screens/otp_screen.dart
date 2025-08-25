// lib/features/auth/screens/otp_screen.dart
import 'dart:async';

import 'package:fatura_yeni/core/services/api_service.dart';
import 'package:fatura_yeni/core/services/storage_service.dart';
import 'package:fatura_yeni/features/main/main_screen.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:pinput/pinput.dart';

class OtpScreen extends StatefulWidget {
  final String verificationId;
  final String email;
  final String password;
  final String phoneNumber;
  final String? displayName;

  const OtpScreen({
    super.key,
    required this.verificationId,
    required this.email,
    required this.password,
    required this.phoneNumber,
    this.displayName,
  });

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final _pinController = TextEditingController();
  final _apiService = ApiService();
  final _storageService = StorageService();
  bool _isLoading = false;

  Future<void> _verifyOtp(String smsCode) async {
    setState(() {
      _isLoading = true;
    });

    try {
      // 1. Gelen SMS kodunu kullanarak Firebase ile kimlik bilgisi oluştur
      final credential = PhoneAuthProvider.credential(
        verificationId: widget.verificationId,
        smsCode: smsCode,
      );

      // 2. Kullanıcıyı Firebase'e kaydet ve ID jetonunu al
      final userCredential =
          await FirebaseAuth.instance.signInWithCredential(credential);
      final firebaseToken = await userCredential.user?.getIdToken();

      if (firebaseToken == null) {
        throw Exception("Firebase'den doğrulama jetonu alınamadı.");
      }

      // 3. Alınan jeton ile kendi backend'imize kayıt isteği at
      final result = await _apiService.registerWithToken(
        firebaseToken: firebaseToken,
        email: widget.email,
        password: widget.password,
        phoneNumber: widget.phoneNumber,
        displayName: widget.displayName,
      );

      // 4. Backend'imizden gelen token'ı sakla ve ana ekrana yönlendir
      if (result['token'] != null) {
        await _storageService.saveToken(result['token']);
        if (mounted) {
          Navigator.of(context).pushAndRemoveUntil(
            MaterialPageRoute(builder: (context) => const MainScreen()),
            (route) => false,
          );
        }
      } else {
        throw Exception(result['message'] ?? 'Sunucuya kayıt başarısız oldu.');
      }
    } on FirebaseAuthException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('OTP Doğrulama Hatası: ${e.message}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Bir hata oluştu: ${e.toString()}')),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Telefon Numarası Doğrulama'),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '${widget.phoneNumber} numarasına gönderilen 6 haneli kodu girin.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 40),
              Pinput(
                controller: _pinController,
                length: 6,
                onCompleted: (pin) => _verifyOtp(pin),
              ),
              const SizedBox(height: 40),
              _isLoading
                  ? const CircularProgressIndicator()
                  : ElevatedButton(
                      onPressed: () {
                        if (_pinController.text.length == 6) {
                          _verifyOtp(_pinController.text);
                        }
                      },
                      child: const Text('Doğrula'),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}
