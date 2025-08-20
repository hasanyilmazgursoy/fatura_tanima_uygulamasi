// lib/features/auth/screens/register_screen.dart

import 'package:fatura_yeni/core/services/api_service.dart';
import 'package:fatura_yeni/core/services/firebase_service.dart';
import 'package:fatura_yeni/core/services/storage_service.dart';
import 'package:fatura_yeni/features/main/main_screen.dart';
import 'package:fatura_yeni/features/auth/screens/otp_screen.dart';
import 'package:flutter/material.dart';
import 'package:intl_phone_field/intl_phone_field.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController(text: "Jimmy Grammy");
  final _emailController = TextEditingController(text: "jimmygrammy@gmail.com");
  final _passwordController = TextEditingController();
  String _fullPhoneNumber = '';

  bool _isPasswordVisible = false;
  bool _isLoading = false;

  final ApiService _apiService = ApiService();
  final FirebaseService _firebaseService = FirebaseService();
  final StorageService _storageService = StorageService();

  Future<void> _register() async {
    if (_formKey.currentState?.validate() != true) {
      return;
    }
    setState(() {
      _isLoading = true;
    });

    try {
      // Bu fonksiyon artık doğrudan kayıt yapmayacak, sadece SMS gönderecek.
      // Token alma işlemi OtpScreen'e taşındı.
      await _firebaseService.getFirebaseIdToken(
        phoneNumber: _fullPhoneNumber,
        onCodeSent: (String verificationId) {
          // SMS başarıyla gönderildiğinde bu blok çalışır.
          // Kullanıcıyı, aldığı verificationId ve diğer form bilgileriyle
          // OtpScreen'e yönlendir.
          if (mounted) {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (context) => OtpScreen(
                  verificationId: verificationId,
                  name: _nameController.text,
                  email: _emailController.text,
                  password: _passwordController.text,
                  fullPhoneNumber: _fullPhoneNumber,
                ),
              ),
            );
          }
        },
      );
      // Not: getFirebaseIdToken'ın bu versiyonu hemen bir token döndürmeyecek,
      // bu yüzden onCodeSent callback'ini bekliyoruz. Hata yönetimi
      // getFirebaseIdToken içindeki completer tarafından yapılıyor.
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hata: ${e.toString()}')),
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
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;

    return Scaffold(
      // Arka plan rengi temadan (açık tema için backgroundLight)
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: EdgeInsets.symmetric(
              horizontal: screenSize.width * 0.08,
              vertical: 24.0,
            ),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(height: screenSize.height * 0.05),
                  _buildHeader(context),
                  SizedBox(height: screenSize.height * 0.07),
                  _buildFormFields(context),
                  const SizedBox(height: 40),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _register,
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Continue'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    // Bu logo, açık arka planlar için tasarlanmış olan
    // login_screen.dart'taki logonun aynısı olabilir.
    return Text(
      "Scanner",
      textAlign: TextAlign.center,
      style: Theme.of(context).textTheme.displayLarge?.copyWith(
            color: Theme.of(context).primaryColor,
            fontSize: 48,
          ),
    );
  }

  Widget _buildFormFields(BuildContext context) {
    final theme = Theme.of(context);
    final labelStyle = theme.textTheme.labelSmall;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Full Name
        Text("Full Name", style: labelStyle),
        TextFormField(
          controller: _nameController,
          decoration: const InputDecoration(hintText: "Enter your full name"),
          validator: (value) =>
              value!.isEmpty ? "Please enter your name" : null,
        ),
        const SizedBox(height: 24),

        // Email Address
        Text("Email Address", style: labelStyle),
        TextFormField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(hintText: "Enter your email"),
          validator: (value) =>
              value!.isEmpty ? "Please enter your email" : null,
        ),
        const SizedBox(height: 24),

        // Phone Number
        Text("Phone Number", style: labelStyle),
        IntlPhoneField(
          initialCountryCode: 'TR', // Nijerya bayrağı için
          decoration: const InputDecoration(
            hintText: 'Phone Number',
          ),
          onChanged: (phone) {
            _fullPhoneNumber = phone.completeNumber;
          },
        ),
        const SizedBox(height: 24),

        // Password
        Text("Password", style: labelStyle),
        TextFormField(
          controller: _passwordController,
          obscureText: !_isPasswordVisible,
          decoration: InputDecoration(
            hintText: "Enter New Password",
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
          validator: (value) => value!.length < 6
              ? "Password must be at least 6 characters"
              : null,
        ),
      ],
    );
  }
}
