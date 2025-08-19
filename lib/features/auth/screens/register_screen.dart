// lib/features/auth/screens/register_screen.dart

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
  final _passwordController = TextEditingController();
  bool _isPasswordVisible = false;

  @override
  void dispose() {
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
                    onPressed: () {
                      // Form geçerliyse OTP ekranına yönlendir
                      if (_formKey.currentState!.validate()) {
                        Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const OtpScreen()),
                        );
                      }
                    },
                    child: const Text('Continue'),
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
          initialValue: "Jimmy Grammy",
          decoration: const InputDecoration(hintText: "Enter your full name"),
          validator: (value) =>
              value!.isEmpty ? "Please enter your name" : null,
        ),
        const SizedBox(height: 24),

        // Email Address
        Text("Email Address", style: labelStyle),
        TextFormField(
          initialValue: "jimmygrammy@gmail.com",
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(hintText: "Enter your email"),
          validator: (value) =>
              value!.isEmpty ? "Please enter your email" : null,
        ),
        const SizedBox(height: 24),

        // Phone Number
        Text("Phone Number", style: labelStyle),
        IntlPhoneField(
          initialCountryCode: 'NG', // Nijerya bayrağı için
          decoration: const InputDecoration(
            hintText: 'Phone Number',
          ),
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
