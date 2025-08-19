// lib/features/account/screens/account_screen.dart
import 'package:fatura_yeni/features/auth/screens/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:fatura_yeni/features/auth/screens/login_register_screen.dart';

class AccountScreen extends StatelessWidget {
  const AccountScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hesap'),
        automaticallyImplyLeading: false,
      ),
      body: Center(
        child: ElevatedButton(
          onPressed: () {
            // Kullanıcıyı giriş ekranına yönlendir ve geri dönememesini sağla
            Navigator.of(context).pushAndRemoveUntil(
              MaterialPageRoute(builder: (context) => const LoginScreen()),
              (Route<dynamic> route) => false,
            );
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.redAccent,
            foregroundColor: Colors.white,
          ),
          child: const Text('Çıkış Yap'),
        ),
      ),
    );
  }
}
