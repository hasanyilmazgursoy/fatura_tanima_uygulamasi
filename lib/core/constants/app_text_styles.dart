// lib/core/constants/app_text_styles.dart

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fatura_yeni/core/constants/app_colors.dart'; // Renklerimizi import ediyoruz

class AppTextStyles {
  // Ana Başlık (Örn: Onboarding ekranlarındaki büyük metinler)
  static TextStyle get displayLarge {
    return GoogleFonts.inter(
      fontSize: 32,
      fontWeight: FontWeight.bold,
      color: AppColors.textLight, // Varsayılan renk
    );
  }

  // Standart Gövde Metni
  static TextStyle get bodyLarge {
    return GoogleFonts.inter(
      fontSize: 16,
      fontWeight: FontWeight.normal,
      color: AppColors.textLight,
    );
  }

  // Buton Metinleri
  static TextStyle get button {
    return GoogleFonts.inter(
      fontSize: 18,
      fontWeight: FontWeight.w600, // Biraz daha kalın
    );
  }

  // Input Alanı Etiketleri (Örn: "Email Address")
  static TextStyle get labelStyle {
    return GoogleFonts.inter(
      fontSize: 14,
      fontWeight: FontWeight.w500,
      color: AppColors.textLight.withOpacity(0.7),
    );
  }
}
