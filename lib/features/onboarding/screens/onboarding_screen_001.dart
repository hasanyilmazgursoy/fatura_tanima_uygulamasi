import 'package:flutter/material.dart';

class OnboardingScreen1 extends StatelessWidget {
  const OnboardingScreen1({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // İllüstrasyon, esnek olması için Expanded içine alındı
        const Expanded(
          flex: 2,
          child: _Illustration(),
        ),
        // Metin, esnek olması için Expanded içine alındı
        Expanded(
          flex: 1,
          child: Text.rich(
            TextSpan(
              // Stil, doğrudan AppTheme'de tanımladığımız displayLarge'dan geliyor.
              style: Theme.of(context)
                  .textTheme
                  .displayLarge
                  ?.copyWith(color: Colors.white),
              children: const [
                TextSpan(text: "Say goodbye "),
                WidgetSpan(
                  alignment: PlaceholderAlignment.middle,
                  child: Padding(
                    padding: EdgeInsets.symmetric(horizontal: 4.0),
                    child: Text("👋", style: TextStyle(fontSize: 32)),
                  ),
                ),
                TextSpan(text: "\nto paper receipts"),
              ],
            ),
            textAlign: TextAlign.center,
          ),
        ),
      ],
    );
  }
}

// İllüstrasyonu daha temiz tutmak için ayrı bir widget'a ayırdık
class _Illustration extends StatelessWidget {
  const _Illustration();

  @override
  Widget build(BuildContext context) {
    const Color scannerGreen = Color(0xFF34D399);

    // FractionallySizedBox, illüstrasyonun her ekranda orantılı kalmasını sağlar
    return FractionallySizedBox(
      widthFactor: 0.8,
      heightFactor: 0.8,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Transform.rotate(
            angle: -0.2, // -12 derece
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24.0),
                boxShadow: const [
                  BoxShadow(
                      color: Colors.black12,
                      blurRadius: 20,
                      offset: Offset(0, 10))
                ],
              ),
            ),
          ),
          Transform.rotate(
            angle: -0.1, // -6 derece
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24.0),
                boxShadow: const [
                  BoxShadow(
                      color: Colors.black12,
                      blurRadius: 20,
                      offset: Offset(0, 10))
                ],
              ),
            ),
          ),
          Container(
            width: 150,
            height: 100,
            decoration: BoxDecoration(
              color: scannerGreen,
              borderRadius: BorderRadius.circular(24.0),
            ),
          ),
        ],
      ),
    );
  }
}
