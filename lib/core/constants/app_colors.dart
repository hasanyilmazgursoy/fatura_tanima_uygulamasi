// lib/core/constants/app_colors.dart

import 'package:flutter/material.dart';

class AppColors {
  // === Ana Renkler (Light & Dark Mode Ortak) ===
  static const Color primaryBlue =
      Color(0xFF1E3A8A); // Ana Koyu Mavi (Onboarding arkaplanı, butonlar)
  static const Color accentGreen =
      Color(0xFF34D399); // Vurgu Yeşili (İkonlar, grafikler)

  // === Light Mode Renkleri ===
  static const Color backgroundLight = Color(0xFFF5F7FA); // Açık Arka Plan
  static const Color textLight = Color(0xFF1A202C); // Açık Mod Metin Rengi
  static const Color white = Colors.white;

  // === Dark Mode Renkleri ===
  static const Color primaryDark = Color(0xFF0D1B2A); // Koyu Arka Plan
  static const Color secondaryDark = Color(0xFF1B263B); // Kart Rengi
  static const Color textDark = Color(0xFFE0E1DD); // Koyu Mod Metin Rengi
}
