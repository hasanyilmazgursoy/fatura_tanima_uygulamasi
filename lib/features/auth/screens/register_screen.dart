// lib/features/auth/screens/register_screen.dart

import 'package:fatura_yeni/core/services/api_service.dart';
import 'package:fatura_yeni/core/services/storage_service.dart';
import 'package:fatura_yeni/features/auth/screens/otp_screen.dart';
import 'package:fatura_yeni/features/main/main_screen.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:intl_phone_field/intl_phone_field.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String _fullPhoneNumber = '';

  bool _isPasswordVisible = false;
  bool _isLoading = false;

  // Firebase Auth servisini başlatalım
  final FirebaseAuth _auth = FirebaseAuth.instance;

  Future<void> _sendOtp() async {
    if (_formKey.currentState?.validate() != true) {
      return;
    }
    if (_fullPhoneNumber.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Lütfen geçerli bir telefon numarası girin.')),
      );
      return;
    }
    setState(() {
      _isLoading = true;
    });

    await _auth.verifyPhoneNumber(
      phoneNumber: _fullPhoneNumber,
      verificationCompleted: (PhoneAuthCredential credential) async {
        // Bu genellikle Android'de otomatik doğrulama durumunda çalışır
        // Bu demoda bu kısmı basit tutuyoruz.
        setState(() {
          _isLoading = false;
        });
      },
      verificationFailed: (FirebaseAuthException e) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Telefon doğrulaması başarısız: ${e.message}')),
        );
      },
      codeSent: (String verificationId, int? resendToken) {
        // Kod başarıyla gönderildiğinde OTP ekranına yönlendir
        Navigator.of(context).push(MaterialPageRoute(
          builder: (context) => OtpScreen(
            verificationId: verificationId,
            email: _emailController.text,
            password: _passwordController.text,
            phoneNumber: _fullPhoneNumber,
            displayName: _nameController.text,
          ),
        ));
        setState(() {
          _isLoading = false;
        });
      },
      codeAutoRetrievalTimeout: (String verificationId) {
        // Otomatik kod alma zaman aşımına uğradığında
      },
    );
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
                    onPressed: _isLoading
                        ? null
                        : _sendOtp, // Buton artık _sendOtp'yi çağırıyor
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Text(
                            'Telefon Numarasını Doğrula'), // Buton metni güncellendi
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
        Text("Ad Soyad", style: labelStyle),
        TextFormField(
          controller: _nameController,
          decoration:
              const InputDecoration(hintText: "Adınızı ve soyadınızı girin"),
          validator: (value) =>
              value!.isEmpty ? "Lütfen adınızı ve soyadınızı girin" : null,
        ),
        const SizedBox(height: 24),

        // Email Address
        Text("E-posta Adresi", style: labelStyle),
        TextFormField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          decoration:
              const InputDecoration(hintText: "E-posta adresinizi girin"),
          validator: (value) =>
              value!.isEmpty ? "Lütfen e-posta adresinizi girin" : null,
        ),
        const SizedBox(height: 24),

        // Phone Number
        Text("Telefon Numarası", style: labelStyle),
        IntlPhoneField(
          initialCountryCode: 'TR',
          decoration: const InputDecoration(
            hintText: 'Telefon Numarası',
          ),
          onChanged: (phone) {
            _fullPhoneNumber = phone.completeNumber;
          },
          // Anlık çökmeyi önlemek için validator'ı kaldırıyoruz.
          // Kontrolü butona basıldığında yapacağız.
          // validator: (phone) {
          //   if (phone == null || !phone.isValidNumber()) {
          //     return 'Lütfen geçerli bir telefon numarası girin.';
          //   }
          //   return null;
          // },
        ),
        const SizedBox(height: 24),

        // Password
        Text("Şifre", style: labelStyle),
        TextFormField(
          controller: _passwordController,
          obscureText: !_isPasswordVisible,
          decoration: InputDecoration(
            hintText: "Yeni şifrenizi girin",
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
          validator: (value) =>
              value!.length < 6 ? "Şifre en az 6 karakter olmalıdır" : null,
        ),
      ],
    );
  }
}
