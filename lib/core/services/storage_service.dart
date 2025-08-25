// lib/core/services/storage_service.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class StorageService {
  final _storage = const FlutterSecureStorage();

  static const _tokenKey = 'auth_token';

  // Backend'den gelen JWT'yi güvenli bir şekilde saklar.
  Future<void> saveToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }

  // Saklanan JWT'yi okur.
  Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }

  // Saklanan JWT'yi siler (çıkış yapma işlemi için).
  Future<void> deleteToken() async {
    await _storage.delete(key: _tokenKey);
  }
}
