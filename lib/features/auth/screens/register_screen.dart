// lib/features/auth/screens/register_screen.dart

import 'package:fatura_yeni/core/services/api_service.dart';
import 'package:fatura_yeni/core/services/firebase_service.dart';
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
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String _fullPhoneNumber = '';

  bool _isPasswordVisible = false;
  bool _isLoading = false;

  final ApiService _apiService = ApiService();
  final FirebaseService _firebaseService = FirebaseService();

  Future<void> _register() async {
    if (_formKey.currentState?.validate() != true) return;
    setState(() => _isLoading = true);

    try {
      // 1) Telefon doğrulamasını başlat; kod gelince OTP ekranına yönlendir
      await _firebaseService.getFirebaseIdToken(
        phoneNumber: _fullPhoneNumber,
        onCodeSent: (String verificationId) {
          if (!mounted) return;
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => OtpScreen(
                verificationId: verificationId,
                name: _nameController.text.trim(),
                email: _emailController.text.trim(),
                password: _passwordController.text,
                fullPhoneNumber: _fullPhoneNumber,
              ),
            ),
          );
        },
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Kayıt başarısız: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
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
    final isWide = screenSize.width >= 900;
    final horizontalPadding = isWide ? 24.0 : screenSize.width * 0.08;
    final topGapFactor = screenSize.height < 700 ? 0.02 : 0.04;
    final betweenGapFactor = screenSize.height < 700 ? 0.04 : 0.06;

    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 520),
                child: SingleChildScrollView(
                  padding: EdgeInsets.symmetric(
                    horizontal: horizontalPadding,
                    vertical: 24.0,
                  ),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SizedBox(height: screenSize.height * topGapFactor),
                        _buildLogo(context),
                        SizedBox(height: screenSize.height * betweenGapFactor),
                        _buildTitle(context),
                        SizedBox(height: screenSize.height * betweenGapFactor),
                        _buildFormFields(context),
                        const SizedBox(height: 32),
                        _buildFooter(context),
                      ],
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildLogo(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final screenSize = MediaQuery.of(context).size;

    // Login ekranı ile aynı logo sistemi - marka kimliği tutarlılığı için
    final String logoPath = isDark
        ? 'assets/logo_light_bg.png' // beyaz zeminli logo (dark modda kontrast iyi)
        : 'assets/logo_dark_bg.png'; // mavi zeminli logo (açık arkaplanda daha doygun görünüm sağlar)

    // Responsive logo boyutu - login ekranı ile aynı
    final logoWidth = screenSize.width < 400
        ? screenSize.width * 0.85 // Küçük ekranlarda ekranın %85'i
        : screenSize.width < 600
            ? screenSize.width * 0.75 // Orta ekranlarda ekranın %75'i
            : screenSize.width < 900
                ? screenSize.width * 0.55 // Büyük ekranlarda ekranın %55'i
                : screenSize.width * 0.45; // Çok büyük ekranlarda ekranın %45'i

    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 20),
        child: Image.asset(
          logoPath,
          width: logoWidth,
          fit: BoxFit.contain,
        ),
      ),
    );
  }

  Widget _buildTitle(BuildContext context) {
    return Text(
      "Hesap Oluştur",
      textAlign: TextAlign.center,
      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            color: const Color(0xFF323232),
            fontWeight: FontWeight.w600, // Bold'dan SemiBold'a düşürdüm
            fontSize: 24,
          ),
    );
  }

  Widget _buildFormFields(BuildContext context) {
    final theme = Theme.of(context);

    final inputBorder = OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: Color(0xFFE0E0E0)),
    );
    final focusedBorder = OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide(color: Theme.of(context).primaryColor, width: 2),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Ad Soyad
        Text("Ad Soyad",
            style: theme.textTheme.labelSmall
                ?.copyWith(color: const Color(0xFF323232), fontSize: 14)),
        const SizedBox(height: 6), // 8'den 6'ya düşürdüm
        SizedBox(
          height: 52,
          child: TextFormField(
            controller: _nameController,
            textAlignVertical: TextAlignVertical.center,
            decoration: InputDecoration(
              hintText: "Adınızı ve soyadınızı girin",
              hintStyle:
                  const TextStyle(color: Color(0xFFB0B0B0)), // Daha açık gri
              isDense: true,
              prefixIcon: const Icon(Icons.person, color: Colors.grey),
              prefixIconConstraints:
                  const BoxConstraints(minWidth: 48, minHeight: 48),
              filled: true,
              fillColor: Colors.white,
              border: inputBorder,
              enabledBorder: inputBorder,
              focusedBorder: focusedBorder,
              contentPadding: const EdgeInsets.symmetric(horizontal: 0),
            ),
            validator: (value) =>
                value!.isEmpty ? "Lütfen adınızı ve soyadınızı girin" : null,
          ),
        ),
        const SizedBox(height: 20),

        // E-posta Adresi
        Text("E-posta Adresi",
            style: theme.textTheme.labelSmall
                ?.copyWith(color: const Color(0xFF323232), fontSize: 14)),
        const SizedBox(height: 6), // 8'den 6'ya düşürdüm
        SizedBox(
          height: 52,
          child: TextFormField(
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
            textAlignVertical: TextAlignVertical.center,
            decoration: InputDecoration(
              hintText: "E-posta adresinizi girin",
              hintStyle:
                  const TextStyle(color: Color(0xFFB0B0B0)), // Daha açık gri
              isDense: true,
              prefixIcon: const Icon(Icons.email, color: Colors.grey),
              prefixIconConstraints:
                  const BoxConstraints(minWidth: 48, minHeight: 48),
              filled: true,
              fillColor: Colors.white,
              border: inputBorder,
              enabledBorder: inputBorder,
              focusedBorder: focusedBorder,
              contentPadding: const EdgeInsets.symmetric(horizontal: 0),
            ),
            validator: (value) =>
                value!.isEmpty ? "Lütfen e-posta adresinizi girin" : null,
          ),
        ),
        const SizedBox(height: 20),

        // Telefon Numarası
        Text("Telefon Numarası",
            style: theme.textTheme.labelSmall
                ?.copyWith(color: const Color(0xFF323232), fontSize: 14)),
        const SizedBox(height: 6), // 8'den 6'ya düşürdüm
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SizedBox(
              height: 52,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFE0E0E0)),
                ),
                child: IntlPhoneField(
                  initialCountryCode: 'TR',
                  disableLengthCheck: false, // 10 hane kontrolü aktif
                  invalidNumberMessage: '', // Hata metnini gizle
                  textAlignVertical: TextAlignVertical.center,
                  autovalidateMode: AutovalidateMode.disabled,
                  decoration: InputDecoration(
                    hintText: 'Telefon numaranızı girin',
                    hintStyle: const TextStyle(color: Color(0xFFB0B0B0)),
                    border: InputBorder.none,
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(color: Color(0xFFE0E0E0)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(
                          color: Theme.of(context).primaryColor, width: 2),
                    ),
                    errorBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(
                          color: Color(
                              0xFFE0E0E0)), // hata halinde de aynı görünüm
                    ),
                    focusedErrorBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(
                          color: Theme.of(context).primaryColor, width: 2),
                    ),
                    errorStyle:
                        const TextStyle(height: 0, color: Colors.transparent),
                    counterText: '', // İç sayaç gizlensin
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 16),
                  ),
                  onChanged: (phone) {
                    _fullPhoneNumber = phone.completeNumber;
                  },
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        // Şifre
        Text("Şifre",
            style: theme.textTheme.labelSmall
                ?.copyWith(color: const Color(0xFF323232), fontSize: 14)),
        const SizedBox(height: 6), // 8'den 6'ya düşürdüm
        SizedBox(
          height: 52,
          child: TextFormField(
            controller: _passwordController,
            obscureText: !_isPasswordVisible,
            textAlignVertical: TextAlignVertical.center,
            decoration: InputDecoration(
              hintText: "Yeni şifrenizi girin",
              hintStyle:
                  const TextStyle(color: Color(0xFFB0B0B0)), // Daha açık gri
              isDense: true,
              prefixIcon: const Icon(Icons.lock, color: Colors.grey),
              prefixIconConstraints:
                  const BoxConstraints(minWidth: 48, minHeight: 48),
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
              filled: true,
              fillColor: Colors.white,
              border: inputBorder,
              enabledBorder: inputBorder,
              focusedBorder: focusedBorder,
              contentPadding: const EdgeInsets.symmetric(horizontal: 0),
            ),
            validator: (value) =>
                value!.length < 6 ? "Şifre en az 6 karakter olmalıdır" : null,
          ),
        ),
      ],
    );
  }

  Widget _buildFooter(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          height: 48,
          child: ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Theme.of(context).primaryColor,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              elevation: 3,
              shadowColor: Colors.black.withValues(alpha: 0.15),
            ),
            onPressed: _isLoading ? null : _register,
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 180),
              child: _isLoading
                  ? const SizedBox(
                      key: ValueKey('progress'),
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Kayıt Ol', key: ValueKey('label')),
            ),
          ),
        ),
        const SizedBox(height: 24),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Zaten hesabınız var mı? ',
              style: TextStyle(color: Color(0xFF323232)),
            ),
            GestureDetector(
              onTap: () {
                Navigator.of(context).pop();
              },
              child: Text(
                'Giriş Yap',
                style: TextStyle(
                  color: Theme.of(context).primaryColor,
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
