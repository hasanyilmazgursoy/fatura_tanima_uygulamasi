// lib/features/auth/screens/login_register_screen.dart

import 'package:flutter/material.dart';
import 'package:fatura_yeni/features/auth/screens/login_screen.dart';
import 'package:fatura_yeni/features/auth/screens/register_screen.dart';

// import 'package:fatura_uygulamasi/features/auth/screens/register_screen.dart';

class LoginRegisterScreen extends StatelessWidget {
  const LoginRegisterScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Merkezi temadan renkleri ve stilleri alıyoruz.
    final theme = Theme.of(context);
    final screenSize = MediaQuery.of(context).size;

    return Scaffold(
      // Arka plan rengi, temadaki birincil renkten (primaryColor) geliyor.
      backgroundColor: theme.primaryColor,
      body: SafeArea(
        child: Padding(
          // Responsive yan boşluklar
          padding: EdgeInsets.symmetric(horizontal: screenSize.width * 0.08),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // DEĞİŞİKLİK: Boşlukları daha dengeli dağıtmak için Spacer flex değerleri güncellendi.
              const Spacer(flex: 3),
              _buildLogoAndTitle(
                  context), // Metot ismi daha açıklayıcı hale getirildi.
              const Spacer(flex: 2),
              _buildButtons(context),
              const Spacer(flex: 1),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLogoAndTitle(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        // DEĞİŞİKLİK: Yeni tasarıma uygun, daha modern ve temiz bir ikon kullanıldı.
        const Icon(
          Icons.receipt_long_outlined,
          size: 65,
          color: Colors.white,
        ),
        const SizedBox(height: 24),
        Text(
          "Scanner",
          style: theme.textTheme.displayLarge?.copyWith(
            color: Colors.white,
            fontSize:
                52, // DEĞİŞİKLİK: Daha vurgulu bir görünüm için font boyutu artırıldı.
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          "No more paper receipt!",
          style: theme.textTheme.bodyLarge?.copyWith(
            color: Colors.white
                .withOpacity(0.85), // DEĞİŞİKLİK: Görünürlük hafifçe artırıldı.
            fontSize: 16,
          ),
        ),
      ],
    );
  }

  Widget _buildButtons(BuildContext context) {
    final theme = Theme.of(context);

    // DEĞİŞİKLİK: Modern ve yumuşak kenarlı buton stili burada tanımlanıyor.
    final buttonShape = MaterialStateProperty.all<OutlinedBorder>(
      const StadiumBorder(), // Kenarları tam yuvarlak (hap şeklinde) yapar.
    );

    return Column(
      children: [
        // Login Butonu
        OutlinedButton(
          style: theme.outlinedButtonTheme.style?.copyWith(
            shape: buttonShape, // Modern şekli uyguluyoruz.
            side: MaterialStateProperty.all(
              const BorderSide(
                  color: Colors.white,
                  width: 2), // Kenar çizgisi kalınlaştırıldı.
            ),
            foregroundColor: MaterialStateProperty.all(Colors.white),
            padding: MaterialStateProperty.all(
              const EdgeInsets.symmetric(
                  vertical: 16), // Buton içi dikey boşluk artırıldı.
            ),
          ),
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const LoginScreen()),
            );
          },
          child: const Text('Login'),
        ),
        const SizedBox(height: 16),

        // Register Butonu
        ElevatedButton(
          style: theme.elevatedButtonTheme.style?.copyWith(
            shape: buttonShape, // Modern şekli uyguluyoruz.
            backgroundColor: MaterialStateProperty.all(Colors.white),
            foregroundColor: MaterialStateProperty.all(theme.primaryColor),
            padding: MaterialStateProperty.all(
              const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
          onPressed: () {
            Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const RegisterScreen()));
          },
          child: const Text('Register'),
        ),
      ],
    );
  }
}
