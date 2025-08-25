// lib/features/dashboard/screens/dashboard_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';

import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'package:fatura_yeni/features/dashboard/models/invoice_model.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<List<Invoice>> _invoicesFuture;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _invoicesFuture = _loadInvoices();
  }

  Future<List<Invoice>> _loadInvoices() async {
    try {
      final String response = await rootBundle
          .loadString('assets/toplu_fatura_raporu_20250818_094942.json');
      final List<dynamic> data = await json.decode(response);
      return data.map((json) => Invoice.fromJson(json)).toList();
    } catch (e) {
      // Handle error appropriately
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load invoices: $e')),
        );
      }
      return [];
    }
  }

  // --- Dosya/Görüntü Seçim Metotları ---

  Future<void> _pickImage(ImageSource source) async {
    try {
      // Kamera sadece tek fotoğraf çekebilir
      if (source == ImageSource.camera) {
        final XFile? pickedFile = await _picker.pickImage(source: source);
        if (pickedFile != null) {
          if (kDebugMode) {
            print('Seçilen resim yolu: ${pickedFile.path}');
          }
          _showSuccessSnackbar('Resim seçildi!');
        }
      } else {
        // Galeri çoklu seçime izin verir
        final List<XFile> pickedFiles = await _picker.pickMultiImage();
        if (pickedFiles.isNotEmpty) {
          if (kDebugMode) {
            for (var file in pickedFiles) {
              print('Seçilen resim yolu: ${file.path}');
            }
          }
          _showSuccessSnackbar('${pickedFiles.length} resim seçildi!');
        }
      }
    } catch (e) {
      if (kDebugMode) {
        print('Resim seçerken hata: $e');
      }
      _showErrorSnackbar('Resim seçilemedi.');
    }
  }

  Future<void> _pickFile() async {
    try {
      final FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'],
        allowMultiple: true,
      );

      if (result != null && result.files.isNotEmpty) {
        // TODO: Seçilen dosyaları işle
        if (kDebugMode) {
          for (var file in result.files) {
            print('Seçilen dosya adı: ${file.name}');
            print('Seçilen dosya yolu: ${file.path}');
          }
        }
        _showSuccessSnackbar('${result.files.length} dosya seçildi!');
      }
    } catch (e) {
      if (kDebugMode) {
        print('Dosya seçerken hata: $e');
      }
      _showErrorSnackbar('Dosya seçilemedi.');
    }
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

  void _showImageSourceActionSheet(BuildContext context) {
    // Mobil platformlar için ModalBottomSheet göster
    if (Platform.isAndroid || Platform.isIOS) {
      showModalBottomSheet(
        context: context,
        builder: (BuildContext context) {
          return SafeArea(
            child: Wrap(
              children: <Widget>[
                ListTile(
                  leading: const Icon(Icons.camera_alt),
                  title: const Text('Kameradan Çek'),
                  onTap: () {
                    Navigator.of(context).pop();
                    _pickImage(ImageSource.camera);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.photo_library),
                  title: const Text('Galeriden Seç'),
                  onTap: () {
                    Navigator.of(context).pop();
                    _pickImage(ImageSource.gallery);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.attach_file),
                  title: const Text('Dosya Seç (PDF, Belge)'),
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
    } else {
      // Web veya Desktop için basit bir diyalog veya doğrudan dosya seçici
      _pickFile();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FutureBuilder<List<Invoice>>(
        future: _invoicesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError ||
              !snapshot.hasData ||
              snapshot.data!.isEmpty) {
            return const Center(
                child: Text("Fişler yüklenemedi veya hiç fiş yok."));
          }

          final invoices = snapshot.data!;
          final todayExpenditure = invoices
              .where((invoice) =>
                  DateUtils.isSameDay(invoice.date, DateTime.now()))
              .fold<double>(0.0, (sum, item) => sum + item.totalAmount);

          return _buildDashboardContent(context, todayExpenditure, invoices);
        },
      ),
    );
  }

  Widget _buildDashboardContent(
      BuildContext context, double todayExpenditure, List<Invoice> invoices) {
    // For reminders, let's take the 2 most recent invoices as an example
    final reminderInvoices = invoices.take(2).toList();

    return CustomScrollView(
      slivers: [
        _buildHeader(context, todayExpenditure),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildSectionTitle(context, 'Hatırlatmalar', onAdd: () {}),
                const SizedBox(height: 10),
                if (reminderInvoices.isNotEmpty)
                  _buildReminderItem(
                    context,
                    '${reminderInvoices[0].sellerName} faturası',
                    'Son Ödeme: ${DateFormat('d MMMM y', 'tr_TR').format(reminderInvoices[0].date)}',
                    isStarred: true,
                  ),
                if (reminderInvoices.length > 1) ...[
                  const SizedBox(height: 10),
                  _buildReminderItem(
                    context,
                    '${reminderInvoices[1].sellerName} faturası',
                    'Son Ödeme: ${DateFormat('d MMMM y', 'tr_TR').format(reminderInvoices[1].date)}',
                  ),
                ],
                const SizedBox(height: 30),
                _buildSectionTitle(context, 'Son Fişler'),
                const SizedBox(height: 10),
                _buildRecentReceipts(context, invoices),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildHeader(BuildContext context, double todayExpenditure) {
    final formatCurrency = NumberFormat.currency(locale: 'tr_TR', symbol: '₺');

    return SliverAppBar(
      expandedHeight: 250.0,
      backgroundColor: Colors.transparent,
      elevation: 0,
      pinned: false,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF2E7DFA), Color(0xFF205DFF)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Stack(
            children: [
              const Positioned(
                left: 20,
                top: 60,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Hoş geldin,',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                    Text(
                      'Kullanıcı!', // Static name for now
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              Positioned(
                bottom: -20,
                left: 20,
                right: 20,
                child: _buildExpenditureCard(
                    context, todayExpenditure, formatCurrency),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildExpenditureCard(BuildContext context, double todayExpenditure,
      NumberFormat formatCurrency) {
    return Card(
      elevation: 8,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(15),
          border: Border(
            bottom: BorderSide(color: Colors.orange.shade700, width: 5),
          ),
        ),
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 25),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'BUGÜNKÜ HARCAMA',
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 12,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.1,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              formatCurrency.format(todayExpenditure),
              style: TextStyle(
                color: Colors.blue[800],
                fontSize: 34,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title,
      {VoidCallback? onAdd}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.bold,
            color: Color(0xFF333333),
          ),
        ),
        if (onAdd != null)
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey.shade400, width: 1.5),
              borderRadius: BorderRadius.circular(8),
            ),
            child: InkWell(
              onTap: onAdd,
              child: const Icon(Icons.add, color: Colors.grey, size: 20),
            ),
          ),
      ],
    );
  }

  Widget _buildReminderItem(
    BuildContext context,
    String title,
    String subtitle, {
    bool isChecked = false,
    bool isStarred = false,
  }) {
    return Row(
      children: [
        Container(
          width: 24,
          height: 24,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isChecked ? Colors.blue[700] : Colors.transparent,
            border: Border.all(
              color: isChecked ? Colors.transparent : Colors.grey.shade400,
              width: 2,
            ),
          ),
          child: isChecked
              ? const Icon(Icons.check, color: Colors.white, size: 16)
              : null,
        ),
        const SizedBox(width: 15),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF333333)),
              ),
              Text(
                subtitle,
                style: TextStyle(fontSize: 14, color: Colors.grey[600]),
              ),
            ],
          ),
        ),
        if (isStarred) const Icon(Icons.star, color: Colors.orange, size: 24),
      ],
    );
  }

  Widget _buildRecentReceipts(BuildContext context, List<Invoice> invoices) {
    return SizedBox(
      height: 160,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: invoices.length + 1, // +1 for the upload card
        separatorBuilder: (context, index) => const SizedBox(width: 15),
        itemBuilder: (context, index) {
          if (index == 0) {
            return _buildUploadCard(context);
          }
          final invoice = invoices[index - 1];
          return _buildReceiptCard(context, invoice);
        },
      ),
    );
  }

  Widget _buildUploadCard(BuildContext context) {
    return Container(
      width: 120,
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: () {
          _showImageSourceActionSheet(context);
        },
        borderRadius: BorderRadius.circular(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.grey[300],
              ),
              child: Icon(Icons.camera_alt_outlined,
                  color: Colors.grey[700], size: 30),
            ),
            const SizedBox(height: 8),
            Text(
              "Fiş Yükle",
              textAlign: TextAlign.center,
              style: TextStyle(
                  color: Colors.grey[700], fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReceiptCard(BuildContext context, Invoice invoice) {
    final formatCurrency = NumberFormat.currency(locale: 'tr_TR', symbol: '₺');
    return Container(
      width: 130,
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            spreadRadius: 1,
            blurRadius: 5,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            DateFormat('d MMMM', 'tr_TR').format(invoice.date),
            style: TextStyle(color: Colors.grey[600], fontSize: 12),
          ),
          const Spacer(),
          Text(
            formatCurrency.format(invoice.totalAmount),
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Color(0xFF333333),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            invoice.sellerName,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: Colors.grey[700], fontSize: 13),
          ),
        ],
      ),
    );
  }
}
