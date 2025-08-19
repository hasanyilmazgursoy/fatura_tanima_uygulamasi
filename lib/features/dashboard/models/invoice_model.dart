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
    // JSON'daki verileri güvenli bir şekilde ayrıştırma
    String seller =
        json['structured']?['satici_firma_unvani'] ?? 'Bilinmeyen Satıcı';
    String dateStr = json['structured']?['fatura_tarihi'] ?? '';
    String totalStr =
        json['structured']?['genel_toplam']?.replaceAll(',', '.') ?? '0.0';

    DateTime parsedDate;
    try {
      // Tarih formatını (örn: 28-12-2022) ayrıştırma
      List<String> dateParts = dateStr.split('-');
      if (dateParts.length == 3) {
        parsedDate = DateTime(
          int.parse(dateParts[2]),
          int.parse(dateParts[1]),
          int.parse(dateParts[0]),
        );
      } else {
        parsedDate = DateTime.now();
      }
    } catch (e) {
      parsedDate = DateTime.now();
    }

    return Invoice(
      sellerName:
          seller.split(' ').take(2).join(' '), // Çok uzun isimleri kısalt
      date: parsedDate,
      totalAmount: double.tryParse(totalStr) ?? 0.0,
    );
  }
}
