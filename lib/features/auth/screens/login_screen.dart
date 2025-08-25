// lib/features/auth/screens/login_screen.dart

import 'package:fatura_yeni/core/services/api_service.dart';
import 'package:fatura_yeni/core/services/storage_service.dart';
import 'package:fatura_yeni/features/auth/screens/register_screen.dart';
import 'package:fatura_yeni/features/main/main_screen.dart';
import 'package:flutter/material.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isPasswordVisible = false;
  bool _isLoading = false;

  final _apiService = ApiService();
  final _storageService = StorageService();

  Future<void> _login() async {
    if (_formKey.currentState?.validate() != true) {
      return;
    }
    setState(() {
      _isLoading = true;
    });

    try {
      final response = await _apiService.login(
        email: _emailController.text,
        password: _passwordController.text,
      );

      // YENİ BACKEND'İN YANITINA GÖRE GÜNCELLENDİ
      if (response['token'] != null && response['user'] != null) {
        await _storageService.saveToken(response['token']);
        if (mounted) {
          Navigator.of(context).pushAndRemoveUntil(
            MaterialPageRoute(builder: (context) => const MainScreen()),
            (Route<dynamic> route) => false,
          );
        }
      } else {
        throw Exception('Giriş başarısız: Sunucudan token alınamadı.');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
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
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Responsive padding için ekran boyutunu alıyoruz.
    final screenSize = MediaQuery.of(context).size;

    // Responsive padding
    final horizontalPadding = screenSize.width * 0.08;

    return Scaffold(
      // Arka plan rengi temadan (light/dark)
      body: SafeArea(
        child: SingleChildScrollView(
          // Klavye açıldığında taşmayı önler
          child: Padding(
            padding: EdgeInsets.symmetric(
              horizontal: horizontalPadding,
              vertical: 24.0,
            ),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(height: screenSize.height * 0.05),
                  _buildLogo(context),
                  SizedBox(height: screenSize.height * 0.1),
                  _buildLoginForm(context),
                  const SizedBox(height: 40),
                  _buildFooter(context),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLogo(BuildContext context) {
    return Text(
      "Scanner",
      textAlign: TextAlign.center,
      style: Theme.of(context).textTheme.displayLarge?.copyWith(
            color: Theme.of(context).primaryColor,
            fontSize: 48,
          ),
    );
  }

  Widget _buildLoginForm(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Email Alanı
        Text("E-posta Adresi", style: theme.textTheme.labelSmall),
        TextFormField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(
            hintText: "E-posta adresinizi girin",
          ),
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Lütfen e-posta adresinizi girin.';
            }
            if (!RegExp(r'^[^@]+@[^@]+\.[^@]+').hasMatch(value)) {
              return 'Lütfen geçerli bir e-posta adresi girin.';
            }
            return null;
          },
        ),
        const SizedBox(height: 24),

        // Şifre Alanı
        Text("Şifre", style: theme.textTheme.labelSmall),
        TextFormField(
          controller: _passwordController,
          obscureText: !_isPasswordVisible,
          decoration: InputDecoration(
            hintText: "Şifrenizi girin",
            suffixIcon: IconButton(
              icon: Icon(
                _isPasswordVisible ? Icons.visibility_off : Icons.visibility,
                color: Colors.grey,
              ),
              onPressed: () {
                setState(() {
                  _isPasswordVisible = !_isPasswordVisible;
                });
              },
            ),
          ),
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Lütfen şifrenizi girin.';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildFooter(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ElevatedButton(
          onPressed: _isLoading ? null : _login,
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: Colors.white),
                )
              : const Text('Giriş Yap'),
        ),
        const SizedBox(height: 16),
        TextButton(
          onPressed: () {/* TODO: Şifremi unuttum ekranı */},
          child: Text(
            "Şifremi Unuttum?",
            style: theme.textTheme.bodyLarge?.copyWith(color: Colors.grey[600]),
          ),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text("Yeni misin? ", style: theme.textTheme.bodyLarge),
            GestureDetector(
              onTap: () {
                Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const RegisterScreen()));
              },
              child: Text(
                "Hesap Oluştur",
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.primaryColor,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }
}
