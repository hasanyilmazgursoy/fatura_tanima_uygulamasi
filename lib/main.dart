// lib/main.dart

import 'package:flutter/material.dart';
import 'package:fatura_yeni/core/theme/app_theme.dart';

import 'package:fatura_yeni/features/main/main_screen.dart';
import 'package:fatura_yeni/l10n/app_localizations.dart';

void main() {
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
      home: const MainScreen(),
    );
  }
}
