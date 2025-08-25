// lib/features/main/main_screen.dart

import 'package:fatura_yeni/features/auth/screens/register_screen.dart';
import 'package:fatura_yeni/features/dashboard/screens/dashboard_screen.dart';
import 'package:fatura_yeni/features/scan/screens/scan_screen.dart';
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
    const ScanScreen(),
    const Text('Expenses Screen'), // TODO: Harcamalar ekranı buraya gelecek
    const AccountScreen(),
  ];

  void _onItemTapped(int index) {
    // Tarama butonu (index 1) için özel davranış
    if (index == 1) {
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const RegisterScreen()),
      );
    } else {
      setState(() {
        _selectedIndex = index;
      });
    }
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
              onDestinationSelected: (index) {
                // Tarama butonu (index 1) için özel davranış
                if (index == 1) {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const ScanScreen()),
                  );
                } else {
                  _onItemTapped(index);
                }
              },
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
      body: Center(
        child: _widgetOptions.elementAt(_selectedIndex),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const ScanScreen()),
          );
        },
        shape: const CircleBorder(),
        child: const Icon(Icons.camera_alt),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      bottomNavigationBar: BottomAppBar(
        shape: const CircularNotchedRectangle(),
        notchMargin: 8.0,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: <Widget>[
            IconButton(
              icon: Icon(Icons.home,
                  color: _selectedIndex == 0
                      ? Theme.of(context).primaryColor
                      : Colors.grey),
              onPressed: () => _onItemTapped(0),
              tooltip: 'Anasayfa',
            ),
            const SizedBox(width: 40), // The space for the FAB
            IconButton(
              icon: Icon(Icons.person,
                  color: _selectedIndex == 2
                      ? Theme.of(context).primaryColor
                      : Colors.grey),
              onPressed: () => _onItemTapped(2), // Index'i 2 olarak güncelledik
              tooltip: 'Hesap',
            ),
          ],
        ),
      ),
    );
  }
}
