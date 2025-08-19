// lib/features/scanner/screens/scanner_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  @override
  Widget build(BuildContext context) {
    final isWeb = kIsWeb;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Fatura Tara'),
        centerTitle: true,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              isWeb ? Icons.upload_file_outlined : Icons.camera_alt_outlined,
              size: 100,
              color: Colors.grey,
            ),
            const SizedBox(height: 20),
            Text(
              isWeb ? 'Dosya Yükleme' : 'Kamera Tarama',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              isWeb
                  ? 'Web\'de dosya yükleme özelliği yakında eklenecek'
                  : 'Mobilde kamera tarama özelliği yakında eklenecek',
              style: const TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 30),
            if (isWeb)
              ElevatedButton.icon(
                onPressed: () {
                  // TODO: Web file picker implementasyonu
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                        content:
                            Text('Dosya yükleme özelliği geliştiriliyor...')),
                  );
                },
                icon: const Icon(Icons.upload_file),
                label: const Text('Dosya Seç'),
              )
            else
              ElevatedButton.icon(
                onPressed: () {
                  // TODO: Kamera implementasyonu
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                        content: Text('Kamera özelliği geliştiriliyor...')),
                  );
                },
                icon: const Icon(Icons.camera_alt),
                label: const Text('Kamerayı Aç'),
              ),
          ],
        ),
      ),
    );
  }
}
