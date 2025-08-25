import 'package:fatura_yeni/features/auth/screens/login_screen.dart';

import 'package:flutter/material.dart';
import 'dart:math' as math; // Döndürme işlemleri için

class OnboardingScreen3 extends StatelessWidget {
  const OnboardingScreen3({super.key});

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.symmetric(
            horizontal: screenSize.width * 0.07,
            vertical: 24.0,
          ),
          child: LayoutBuilder(
            builder: (context, constraints) {
              return Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    height: constraints.maxHeight * 0.4,
                    child: _buildIllustration(),
                  ),
                  SizedBox(
                    height: constraints.maxHeight * 0.3,
                    child: _buildContent(context),
                  ),
                  SizedBox(
                    height: constraints.maxHeight * 0.3,
                    child: _buildButtons(context),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  // İllüstrasyon, ikinci ekranla aynı olduğu için kodu tekrar kullanıyoruz.
  Widget _buildIllustration() {
    const Color pinkBar = Color(0xFFF9A8D4);
    const Color yellowBar = Color(0xFFFBBF24);
    const Color greenBar = Color(0xFF34D399);
    const Color purpleLine = Color(0xFF5B21B6);

    return FractionallySizedBox(
      widthFactor: 0.9,
      heightFactor: 0.9,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Positioned(
            top: 32,
            right: 32,
            child: Transform.rotate(
              angle: -math.pi / 4,
              child: const Icon(Icons.trending_up, color: purpleLine, size: 64),
            ),
          ),
          Positioned(
            bottom: 0,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                    width: 64,
                    height: 80,
                    decoration: BoxDecoration(
                        color: pinkBar,
                        borderRadius: const BorderRadius.vertical(
                            top: Radius.circular(8)))),
                const SizedBox(width: 16),
                Container(
                    width: 64,
                    height: 128,
                    decoration: BoxDecoration(
                        color: yellowBar,
                        borderRadius: const BorderRadius.vertical(
                            top: Radius.circular(8)))),
                const SizedBox(width: 16),
                Container(
                    width: 64,
                    height: 176,
                    decoration: BoxDecoration(
                        color: greenBar,
                        borderRadius: const BorderRadius.vertical(
                            top: Radius.circular(8)))),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // Metin içeriğini bu ekrana göre güncelliyoruz.
  Widget _buildContent(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Spacer(),
        Text(
          'Track your\nfinancial growth', // YENİ METİN
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.displayLarge,
        ),
        const Spacer(),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildDot(isActive: false, context: context),
            const SizedBox(width: 20),
            _buildDot(isActive: false, context: context),
            const SizedBox(width: 20),
            _buildDot(
                isActive: true, context: context), // AKTİF NOKTA GÜNCELLENDİ
          ],
        ),
        const Spacer(),
      ],
    );
  }

  Widget _buildDot({required bool isActive, required BuildContext context}) {
    return Container(
      width: 10,
      height: 10,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Theme.of(context)
            .colorScheme
            .onPrimary
            .withOpacity(isActive ? 1.0 : 0.3),
      ),
    );
  }

  Widget _buildButtons(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        ElevatedButton(
          onPressed: () {
            // Artık Login/Register ekranına yönlendirme zamanı
            // Navigator.pushNamed(context, '/login-register');
          },
          child: const Text('Get Started'),
        ),
        const SizedBox(height: 16),
        OutlinedButton(
          onPressed: () {
            Navigator.of(context)
                .push(MaterialPageRoute(builder: (_) => const LoginScreen()));
          },
          child: const Text('Login'),
        ),
      ],
    );
  }
}
