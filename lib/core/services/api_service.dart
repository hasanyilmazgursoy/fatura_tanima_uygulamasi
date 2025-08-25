// lib/core/services/api_service.dart
import 'dart:convert';
import 'package:fatura_yeni/core/services/storage_service.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart'; // Bu paketi ekleyin

class ApiService {
  // TODO: Bu URL'i kendi yerel ağ IP adresinizle güncelleyin.
  // Windows: ipconfig, Mac/Linux: ifconfig
  static const String _baseUrl =
      "http://192.168.137.1:5000"; // Fiziksel cihaz testi için bilgisayarın Hotspot IP'si
  final StorageService _storageService = StorageService();

  // OTP'siz, doğrudan kayıt (ARTIK KULLANILMIYOR)
  /*
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String phoneNumber,
    String? displayName,
  }) async {
    final response = await http.post(
      Uri.parse("$_baseUrl/api/auth/register"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "email": email,
        "password": password,
        "phoneNumber": phoneNumber,
        "displayName": displayName,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      final errorBody = jsonDecode(response.body);
      throw Exception(
          'Kayıt başarısız: ${errorBody['message'] ?? response.body}');
    }
  }
  */

  // YENİ: Firebase Jetonu ile Kayıt
  Future<Map<String, dynamic>> registerWithToken({
    required String firebaseToken,
    required String email,
    required String password,
    required String phoneNumber,
    String? displayName,
  }) async {
    final response = await http.post(
      Uri.parse("$_baseUrl/api/auth/register-with-token"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "firebaseToken": firebaseToken,
        "email": email,
        "password": password,
        "phoneNumber": phoneNumber,
        "displayName": displayName,
      }),
    );

    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      final errorBody = jsonDecode(response.body);
      throw Exception(
          'Sunucuya kayıt başarısız: ${errorBody['message'] ?? response.body}');
    }
  }

  // Giriş işlemi
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse("$_baseUrl/api/auth/login"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({"email": email, "password": password}),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      final errorBody = jsonDecode(response.body);
      throw Exception(
          'Giriş başarısız: ${errorBody['message'] ?? response.body}');
    }
  }

  // Korumalı endpoint'e istek (kullanıcı bilgilerini alma)
  Future<Map<String, dynamic>> getMe(String jwt) async {
    final response = await http.get(
      Uri.parse("$_baseUrl/api/me"),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $jwt'
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      final errorBody = jsonDecode(response.body);
      throw Exception(
          'Kullanıcı bilgileri alınamadı: ${errorBody['message'] ?? response.body}');
    }
  }

  // YENİ: Fatura Yükleme ve İşleme Fonksiyonu
  Future<Map<String, dynamic>> uploadAndParseInvoice(String filePath) async {
    final token = await _storageService.getToken();
    if (token == null) {
      throw Exception('Yetkilendirme jetonu bulunamadı.');
    }

    final uri = Uri.parse("$_baseUrl/api/invoices/parse");
    final request = http.MultipartRequest('POST', uri);

    // Başlıkları ayarla
    request.headers['Authorization'] = 'Bearer $token';
    request.headers['Content-Type'] = 'multipart/form-data';

    // Dosyayı isteğe ekle
    final file = await http.MultipartFile.fromPath(
      'invoiceFile', // Backend'deki router'da belirttiğimiz isimle aynı olmalı
      filePath,
      contentType: MediaType('application',
          'octet-stream'), // Dosya türüne göre dinamik de olabilir
    );
    request.files.add(file);

    try {
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        final errorBody = jsonDecode(response.body);
        throw Exception(
            'Fatura yükleme başarısız: ${errorBody['message'] ?? response.body}');
      }
    } catch (e) {
      print("Fatura yükleme hatası: $e");
      throw Exception('Fatura yüklenirken bir hata oluştu: ${e.toString()}');
    }
  }
}
