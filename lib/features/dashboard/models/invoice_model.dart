// lib/features/dashboard/models/invoice_model.dart

class Invoice {
  final String sellerName;
  final DateTime date;
  final double totalAmount;

  Invoice({
    required this.sellerName,
    required this.date,
    required this.totalAmount,
  });

  // JSON'dan Invoice nesnesine dönüştürme
  factory Invoice.fromJson(Map<String, dynamic> json) {
    final structuredData = json['structured'] as Map<String, dynamic>? ?? {};

    String seller = structuredData['satici_vergi_dairesi'] as String? ??
        structuredData['satici_firma_unvani'] as String? ??
        'Bilinmeyen Satıcı';

    String dateStr = structuredData['fatura_tarihi'] as String? ?? '';
    String totalStr = (structuredData['genel_toplam'] as String? ?? '0.0')
        .replaceAll('.', '')
        .replaceAll(',', '.');

    DateTime parsedDate;
    try {
      if (dateStr.contains('-')) {
        final parts = dateStr.split('-');
        if (parts.length == 3) {
          parsedDate = DateTime(
              int.parse(parts[2]), int.parse(parts[1]), int.parse(parts[0]));
        } else {
          parsedDate = DateTime.now();
        }
      } else if (dateStr.contains('.')) {
        final parts = dateStr.split('.');
        if (parts.length == 3) {
          parsedDate = DateTime(
              int.parse(parts[2]), int.parse(parts[1]), int.parse(parts[0]));
        } else {
          parsedDate = DateTime.now();
        }
      } else {
        parsedDate = DateTime.now();
      }
    } catch (e) {
      parsedDate = DateTime.now();
    }

    return Invoice(
      sellerName: seller,
      date: parsedDate,
      totalAmount: double.tryParse(totalStr) ?? 0.0,
    );
  }
}
