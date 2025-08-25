// lib/main.dart

import 'package:fatura_yeni/features/auth/screens/login_screen.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:fatura_yeni/core/theme/app_theme.dart';

import 'package:fatura_yeni/features/main/main_screen.dart';
import 'package:fatura_yeni/l10n/app_localizations.dart';
import 'package:fatura_yeni/firebase_options.dart';
import 'package:fatura_yeni/features/auth/screens/register_screen.dart';

void main() async {
  try {
    WidgetsFlutterBinding.ensureInitialized();
    await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform);
  } catch (e) {
    // Firebase başlatma sırasında bir hata olursa, bunu konsola yazdır.
    // Bu, siyah ekran sorunlarını teşhis etmek için önemlidir.
    debugPrint("Firebase initialization failed: $e");
  }
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Scanner App',
      debugShowCheckedModeBanner: false,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: AppTheme.lightTheme, // Your light theme
      darkTheme: AppTheme.darkTheme, // Your dark theme
      themeMode:
          ThemeMode.system, // Automatically switch based on system settings
      home: const LoginScreen(),
    );
  }
}
