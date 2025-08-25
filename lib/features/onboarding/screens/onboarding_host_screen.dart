// lib/features/onboarding/screens/onboarding_host_screen.dart

import 'package:flutter/material.dart';
import 'package:fatura_yeni/features/auth/screens/login_screen.dart';

// Her bir onboarding sayfasının içeriğini tutacak basit bir model
class OnboardingPageModel {
  final String title;
  final Widget
      illustration; // İllüstrasyonlar farklı olacağı için Widget olarak alıyoruz

  OnboardingPageModel({required this.title, required this.illustration});
}

class OnboardingHostScreen extends StatefulWidget {
  const OnboardingHostScreen({super.key});

  @override
  State<OnboardingHostScreen> createState() => _OnboardingHostScreenState();
}

class _OnboardingHostScreenState extends State<OnboardingHostScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  // Sayfa verilerini merkezi bir listede tutuyoruz
  final List<OnboardingPageModel> _pages = [
    OnboardingPageModel(
      title: "Say goodbye 👋\nto paper receipts",
      illustration:
          const OnboardingIllustration1(), // onboarding_screen_001'den gelen widget
    ),
    OnboardingPageModel(
      title: "Monitor your\ndaily spending",
      illustration:
          const OnboardingIllustration2(), // onboarding_screen_002'den gelen widget
    ),
    OnboardingPageModel(
      title: "Easily access your\nreceipts anywhere",
      illustration:
          const OnboardingIllustration3(), // Bu yeni bir illüstrasyon olacak
    ),
  ];

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _onNextPage() {
    if (_currentPage < _pages.length - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOut,
      );
    } else {
      // Son sayfadaysa Login ekranına git
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    // Tema renklerini ve stillerini alıyoruz
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.primaryColor, // Arka plan rengi temadan
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 24.0),
          child: Column(
            children: [
              // Sayfaların gösterildiği alan
              Expanded(
                flex: 7,
                child: PageView.builder(
                  controller: _pageController,
                  itemCount: _pages.length,
                  onPageChanged: (index) {
                    setState(() {
                      _currentPage = index;
                    });
                  },
                  itemBuilder: (context, index) {
                    final page = _pages[index];
                    // Her sayfanın içeriğini merkezi olarak oluşturuyoruz
                    return Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Expanded(flex: 2, child: page.illustration),
                        Expanded(
                          flex: 1,
                          child: Text(
                            page.title,
                            textAlign: TextAlign.center,
                            style: theme.textTheme.displayLarge?.copyWith(
                              color: theme.colorScheme.onPrimary, // Beyaz metin
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),

              // Alt kısım: Noktalar ve Butonlar
              Expanded(
                flex: 3,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildDotsIndicator(context),
                    _buildButtons(context),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDotsIndicator(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(_pages.length, (index) {
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: index == _currentPage
                  ? Colors.white
                  : Colors.white.withOpacity(0.3),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildButtons(BuildContext context) {
    // Temadan OutlinedButton stilini alıp özelleştiriyoruz
    final outlinedButtonStyle = Theme.of(context).outlinedButtonTheme.style;

    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ElevatedButton(
          style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: Theme.of(context).primaryColor),
          onPressed: _onNextPage,
          child: const Text('Get Started'),
        ),
        const SizedBox(height: 16),
        OutlinedButton(
          style: outlinedButtonStyle?.copyWith(
            side: MaterialStateProperty.all(
                const BorderSide(color: Colors.white)),
            foregroundColor: MaterialStateProperty.all(Colors.white),
          ),
          onPressed: () {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const LoginScreen()),
            );
          },
          child: const Text('Login'),
        ),
      ],
    );
  }
}

// İllüstrasyon Widget'larını ayrı dosyalarda veya bu dosyanın altında tutabilirsiniz.
class OnboardingIllustration1 extends StatelessWidget {
  const OnboardingIllustration1({super.key});
  @override
  Widget build(BuildContext context) {
    return const Center(
        child: Icon(Icons.receipt_long, color: Colors.white, size: 150));
  }
}

class OnboardingIllustration2 extends StatelessWidget {
  const OnboardingIllustration2({super.key});
  @override
  Widget build(BuildContext context) {
    return const Center(
        child: Icon(Icons.bar_chart, color: Colors.white, size: 150));
  }
}

class OnboardingIllustration3 extends StatelessWidget {
  const OnboardingIllustration3({super.key});
  @override
  Widget build(BuildContext context) {
    return const Center(
        child: Icon(Icons.location_on, color: Colors.white, size: 150));
  }
}
