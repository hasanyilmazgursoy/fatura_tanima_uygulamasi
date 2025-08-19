// lib/features/main/main_screen.dart

import 'package:fatura_yeni/features/dashboard/screens/dashboard_screen.dart';
import 'package:fatura_yeni/features/scanner/screens/scanner_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:fatura_yeni/features/account/screens/account_screen.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;

  // Bottom Navigasyon'da gösterilecek ekranlar
  static final List<Widget> _widgetOptions = <Widget>[
    const DashboardScreen(),
    const ScannerScreen(),
    const Text('Expenses Screen'), // TODO: Harcamalar ekranı buraya gelecek
    const AccountScreen(), // TODO: Hesap ekranı buraya gelecek
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isWeb = kIsWeb;
    final screenWidth = MediaQuery.of(context).size.width;
    final isDesktop = screenWidth > 900;

    // Web ve desktop için responsive layout
    if (isWeb && isDesktop) {
      return Scaffold(
        body: Row(
          children: [
            // Sol navigasyon menüsü (desktop web için)
            NavigationRail(
              selectedIndex: _selectedIndex,
              onDestinationSelected: _onItemTapped,
              labelType: NavigationRailLabelType.all,
              destinations: const [
                NavigationRailDestination(
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home),
                  label: Text('Anasayfa'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.camera_alt_outlined),
                  selectedIcon: Icon(Icons.camera_alt),
                  label: Text('Tarama'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.receipt_long_outlined),
                  selectedIcon: Icon(Icons.receipt_long),
                  label: Text('Harcamalar'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.person_outlined),
                  selectedIcon: Icon(Icons.person),
                  label: Text('Hesap'),
                ),
              ],
            ),
            const VerticalDivider(thickness: 1, width: 1),
            // Ana içerik alanı
            Expanded(
              child: _widgetOptions.elementAt(_selectedIndex),
            ),
          ],
        ),
      );
    }

    // Mobil ve küçük ekranlar için bottom navigation
    return Scaffold(
      body: _widgetOptions.elementAt(_selectedIndex),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Anasayfa'),
          BottomNavigationBarItem(
              icon: Icon(Icons.camera_alt), label: 'Tarama'),
          BottomNavigationBarItem(
              icon: Icon(Icons.receipt_long), label: 'Harcamalar'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Hesap'),
        ],
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        selectedItemColor: Theme.of(context).primaryColor,
        unselectedItemColor: Colors.grey,
        showUnselectedLabels: true,
      ),
    );
  }
}
