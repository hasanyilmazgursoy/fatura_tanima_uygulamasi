// lib/features/auth/screens/login_screen.dart

import 'package:fatura_yeni/features/auth/screens/register_screen.dart';
import 'package:flutter/material.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController(text: "jimmygrammy@gmail.com");
  final _passwordController = TextEditingController();
  bool _isPasswordVisible = false;

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
        Text("Email Address", style: theme.textTheme.labelSmall),
        TextFormField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(
            hintText: "jimmygrammy@gmail.com",
          ),
        ),
        const SizedBox(height: 24),

        // Şifre Alanı
        Text("Password", style: theme.textTheme.labelSmall),
        TextFormField(
          controller: _passwordController,
          obscureText: !_isPasswordVisible,
          decoration: InputDecoration(
            hintText: "Enter your password",
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
          onPressed: () {/* TODO: Login işlemi */},
          child: const Text('Login'),
        ),
        const SizedBox(height: 16),
        TextButton(
          onPressed: () {/* TODO: Şifremi unuttum ekranı */},
          child: Text(
            "Forgot Password?",
            style: theme.textTheme.bodyLarge?.copyWith(color: Colors.grey[600]),
          ),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text("New User? ", style: theme.textTheme.bodyLarge),
            GestureDetector(
              onTap: () {
                Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const RegisterScreen()));
              },
              child: Text(
                "Create Account",
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
