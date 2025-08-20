// lib/core/services/firebase_service.dart
import 'dart:async';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart'; // getCodeFromUI için context gerekebilir.

class FirebaseService {
  final FirebaseAuth _auth = FirebaseAuth.instance;

  // UI'dan SMS kodunu almak için bir metot (UI'da implemente edilecek)
  Future<String> _getCodeFromUI(BuildContext context) async {
    // Bu kısım, OTP ekranında bir dialog veya yeni bir sayfa göstererek
    // kullanıcıdan SMS kodunu girmesini isteyecek.
    // Şimdilik sadece bir placeholder.
    // Örnek: return await showOtpDialog(context);
    // TODO: UI'da SMS kodu giriş mekanizmasını oluştur.
    return "123456"; // Geçici test kodu
  }

  Future<void> resendOtp(String phoneNumber) async {
    await _auth.verifyPhoneNumber(
      phoneNumber: phoneNumber,
      verificationCompleted: (PhoneAuthCredential credential) async {
        // Bu genellikle otomatik doğrulama durumunda tetiklenir.
        // Bu senaryoda ele almamıza gerek olmayabilir.
      },
      verificationFailed: (FirebaseAuthException e) {
        // Hata durumunu ele al
        debugPrint("OTP yeniden gönderme hatası: ${e.message}");
        throw e;
      },
      codeSent: (String verificationId, int? resendToken) {
        // Kod tekrar gönderildi. Kullanıcıya bilgi verilebilir.
        debugPrint("Doğrulama kodu tekrar gönderildi: $verificationId");
      },
      codeAutoRetrievalTimeout: (String verificationId) {
        // Otomatik kod alma zaman aşımına uğradı.
      },
      timeout: const Duration(seconds: 120),
    );
  }

  Future<String?> getFirebaseIdTokenWithSmsCode(
      String verificationId, String smsCode) async {
    try {
      final AuthCredential credential = PhoneAuthProvider.credential(
        verificationId: verificationId,
        smsCode: smsCode,
      );

      final UserCredential userCredential =
          await _auth.signInWithCredential(credential);

      final String? idToken = await userCredential.user?.getIdToken();
      return idToken;
    } catch (e) {
      debugPrint("Firebase SMS kodu ile token alma hatası: ${e.toString()}");
      return null;
    }
  }

  Future<String?> getFirebaseIdToken({
    required String phoneNumber,
    required Function(String verificationId) onCodeSent,
  }) async {
    try {
      Completer<String?> completer = Completer<String?>();

      await _auth.verifyPhoneNumber(
        phoneNumber: phoneNumber,
        verificationCompleted: (PhoneAuthCredential credential) async {
          // Bu callback, bazı Android cihazlarda kodun otomatik olarak
          // doğrulanması durumunda tetiklenir.
          final UserCredential userCredential =
              await _auth.signInWithCredential(credential);
          final String? idToken = await userCredential.user?.getIdToken();
          if (!completer.isCompleted) {
            completer.complete(idToken);
          }
        },
        verificationFailed: (FirebaseAuthException e) {
          debugPrint("Firebase doğrulama hatası: ${e.message}");
          if (!completer.isCompleted) {
            completer.completeError(e);
          }
        },
        codeSent: (String verificationId, int? resendToken) {
          // Bu callback, SMS gönderildiğinde tetiklenir.
          // UI'ın OTP girmesini sağlamak için verificationId'yi geri gönderiyoruz.
          onCodeSent(verificationId);
          // Bu noktada token'ı henüz alamadığımız için bekliyoruz.
          // Kullanıcının SMS kodunu girmesi gerekiyor.
        },
        codeAutoRetrievalTimeout: (String verificationId) {
          // Otomatik doğrulama zaman aşımına uğradığında tetiklenir.
          // Genellikle bu durumda bir şey yapmamız gerekmez.
        },
        timeout: const Duration(seconds: 120),
      );

      return completer.future;
    } catch (e) {
      debugPrint("getFirebaseIdToken Hatası: ${e.toString()}");
      return null;
    }
  }

  Future<void> signOut() async {
    await _auth.signOut();
  }
}
