// lib/core/services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Android Emülatör için backend URL'i
  // Gerçek cihazda test ederken kendi LAN IP adresinizi kullanın.
  static const String _baseUrl = "http://192.168.4.73:5000";

  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String phone,
    required String firebaseIdToken,
  }) async {
    final resp = await http.post(
      Uri.parse("$_baseUrl/api/auth/register"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "email": email,
        "password": password,
        "phoneNumber": phone,
        "firebaseIdToken": firebaseIdToken,
      }),
    );
    if (resp.statusCode != 200) throw Exception(resp.body);
    return jsonDecode(resp.body); // { token, user: {...} }
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final resp = await http.post(
      Uri.parse("$_baseUrl/api/auth/login"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({"email": email, "password": password}),
    );
    if (resp.statusCode != 200) throw Exception(resp.body);
    return jsonDecode(resp.body); // { token, user: {...} }
  }

  Future<Map<String, dynamic>> resetPassword({
    required String email,
    required String newPassword,
    required String phone,
    required String firebaseIdToken,
  }) async {
    final resp = await http.post(
      Uri.parse("$_baseUrl/api/auth/reset-password"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "email": email,
        "newPassword": newPassword,
        "firebaseIdToken": firebaseIdToken,
      }),
    );
    if (resp.statusCode != 200) throw Exception(resp.body);
    return jsonDecode(resp.body); // { ok: true, token? }
  }

  Future<Map<String, dynamic>> getMe(String jwt) async {
    final resp = await http.get(
      Uri.parse("$_baseUrl/api/me"),
      headers: {'Authorization': 'Bearer $jwt'},
    );
    if (resp.statusCode != 200) throw Exception(resp.body);
    return jsonDecode(resp.body); // { ok: true, user: {...} }
  }
}
