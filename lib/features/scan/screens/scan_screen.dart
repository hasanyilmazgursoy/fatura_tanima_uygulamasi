import 'dart:io';

import 'package:camera/camera.dart';
import 'package:file_picker/file_picker.dart';
import 'package:fatura_yeni/core/services/api_service.dart'; // ApiService import
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  late List<CameraDescription> _cameras;
  CameraController? _controller;
  Future<void>? _initializeControllerFuture;
  final ImagePicker _picker = ImagePicker();

  // --- YENİ EKLENEN STATE'LER ---
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  Map<String, dynamic>? _parsedData;
  String? _previewImagePath;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras.isNotEmpty) {
        _controller = CameraController(
          _cameras[0],
          ResolutionPreset.high,
          enableAudio: false,
        );
        _initializeControllerFuture = _controller!.initialize();
        if (mounted) {
          setState(() {});
        }
      } else {
        _showErrorSnackbar('Kullanılabilir kamera bulunamadı.');
      }
    } catch (e) {
      _showErrorSnackbar('Kamera başlatılırken bir hata oluştu: $e');
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  // --- YENİ: Dosya Yükleme ve İşleme Fonksiyonu ---
  Future<void> _uploadFile(String filePath) async {
    setState(() {
      _isLoading = true;
      _parsedData = null;
      _previewImagePath = filePath; // Önizleme için dosya yolunu sakla
    });

    try {
      final result = await _apiService.uploadAndParseInvoice(filePath);
      setState(() {
        _parsedData = result;
      });
      _showSuccessSnackbar('Fatura başarıyla işlendi!');
      // Sonuçları göstermek için bir dialog aç
      _showResultDialog();
    } catch (e) {
      _showErrorSnackbar('Hata: ${e.toString()}');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _takePicture() async {
    try {
      await _initializeControllerFuture;
      if (!_controller!.value.isTakingPicture) {
        final XFile file = await _controller!.takePicture();
        // Çekilen fotoğrafı işle
        _uploadFile(file.path);
      }
    } catch (e) {
      _showErrorSnackbar('Fotoğraf çekilirken hata oluştu: $e');
    }
  }

  Future<void> _pickImageFromGallery() async {
    try {
      // Sadece tek bir resim seçtiriyoruz
      final XFile? pickedFile =
          await _picker.pickImage(source: ImageSource.gallery);
      if (pickedFile != null) {
        // Seçilen resmi işle
        _uploadFile(pickedFile.path);
      }
    } catch (e) {
      _showErrorSnackbar('Resim seçilemedi.');
    }
  }

  Future<void> _pickFile() async {
    try {
      final FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
        allowMultiple: false, // Tek dosya seçimi
      );

      if (result != null && result.files.single.path != null) {
        // Seçilen dosyayı işle
        _uploadFile(result.files.single.path!);
      }
    } catch (e) {
      _showErrorSnackbar('Dosya seçilemedi.');
    }
  }

  void _showUploadOptions() {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return SafeArea(
          child: Wrap(
            children: <Widget>[
              ListTile(
                leading: const Icon(Icons.photo_library),
                title: const Text('Galeriden Fotoğraf Seç'),
                onTap: () {
                  Navigator.of(context).pop();
                  _pickImageFromGallery();
                },
              ),
              ListTile(
                leading: const Icon(Icons.attach_file),
                title: const Text('Belge Seç (PDF, JPG, PNG)'),
                onTap: () {
                  Navigator.of(context).pop();
                  _pickFile();
                },
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fatura Tara'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      backgroundColor: Colors.black,
      body: _isLoading
          ? _buildLoadingIndicator() // Yükleniyorsa gösterge göster
          : _buildCameraPreview(),
    );
  }

  // --- YENİ: Yükleme Göstergesi ---
  Widget _buildLoadingIndicator() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 20),
          const Text(
            'Faturanız işleniyor...',
            style: TextStyle(color: Colors.white, fontSize: 16),
          ),
          const SizedBox(height: 20),
          if (_previewImagePath != null)
            SizedBox(
              height: 200,
              child: Image.file(File(_previewImagePath!)),
            ),
        ],
      ),
    );
  }

  // --- YENİ: Sonuçları Gösteren Dialog ---
  void _showResultDialog() {
    if (_parsedData == null) return;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Fatura Analiz Sonucu'),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView(
            shrinkWrap: true,
            children: _parsedData!.entries.map((entry) {
              final key = entry.key.replaceAll('_', ' ').toUpperCase();
              final value = entry.value.toString();
              return ListTile(
                title: Text(key),
                subtitle: Text(value),
              );
            }).toList(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Kapat'),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraPreview() {
    if (_controller == null || _initializeControllerFuture == null) {
      return const Center(
        child: Text(
          'Kamera başlatılıyor...',
          style: TextStyle(color: Colors.white),
        ),
      );
    }

    return FutureBuilder<void>(
      future: _initializeControllerFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.done) {
          return Stack(
            fit: StackFit.expand,
            children: [
              Center(
                child: CameraPreview(_controller!),
              ),
              _buildControls(),
            ],
          );
        } else {
          return const Center(child: CircularProgressIndicator());
        }
      },
    );
  }

  Widget _buildControls() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        Container(
          padding: const EdgeInsets.all(20.0),
          color: Colors.black.withOpacity(0.5),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              IconButton(
                icon: const Icon(Icons.collections,
                    color: Colors.white, size: 30),
                onPressed: _showUploadOptions,
                tooltip: 'Galeriden Yükle',
              ),
              GestureDetector(
                onTap: _takePicture,
                child: Container(
                  width: 70,
                  height: 70,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white,
                    border: Border.all(color: Colors.grey, width: 3),
                  ),
                ),
              ),
              // Spacer to balance the layout
              const SizedBox(width: 48),
            ],
          ),
        ),
      ],
    );
  }

  void _showSuccessSnackbar(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  void _showErrorSnackbar(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
