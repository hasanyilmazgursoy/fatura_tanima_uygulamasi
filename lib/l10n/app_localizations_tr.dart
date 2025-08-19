// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Turkish (`tr`).
class AppLocalizationsTr extends AppLocalizations {
  AppLocalizationsTr([String locale = 'tr']) : super(locale);

  @override
  String get dashboardTitle => 'Anasayfa';

  @override
  String welcomeBack(String name) {
    return 'Hoş geldin, $name!';
  }

  @override
  String get todayExpenditure => 'Bugünkü Harcama';

  @override
  String get reminders => 'Hatırlatmalar';

  @override
  String get receipts => 'Son Fişler';
}
