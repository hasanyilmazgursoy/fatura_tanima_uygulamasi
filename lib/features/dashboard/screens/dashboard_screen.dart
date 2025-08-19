// lib/features/dashboard/screens/dashboard_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';

import 'package:fatura_yeni/features/dashboard/models/invoice_model.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<List<Invoice>> _invoicesFuture;

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
    return CustomScrollView(
      slivers: [
        _buildHeader(context, todayExpenditure),
        SliverList(
          delegate: SliverChildListDelegate(
            [
              Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSectionTitle(context, 'Reminder', onAdd: () {}),
                    const SizedBox(height: 10),
                    _buildReminderItem(
                      context,
                      'Get Receipts up-to-date',
                      'Due on July 29, 2020',
                      isChecked: true,
                      isStarred: true,
                    ),
                    const SizedBox(height: 10),
                    _buildReminderItem(
                      context,
                      'Export Expenses Stats',
                      'Due on July 20, 2020',
                    ),
                    const SizedBox(height: 30),
                    _buildSectionTitle(context, 'Receipts'),
                    const SizedBox(height: 10),
                    _buildRecentReceipts(context, invoices),
                  ],
                ),
              ),
            ],
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
                      'Welcome back,',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                    Text(
                      'Jimmy!',
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
              'TODAY\'S EXPENDITURE',
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
    // Take first 5 for example
    final recentInvoices = invoices.take(5).toList();

    return SizedBox(
      height: 160,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: recentInvoices.length + 1,
        separatorBuilder: (context, index) => const SizedBox(width: 15),
        itemBuilder: (context, index) {
          if (index == 0) {
            return _buildUploadCard(context);
          }
          final invoice = recentInvoices[index - 1];
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
          // TODO: Implement receipt upload
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
              "Upload Receipt",
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
