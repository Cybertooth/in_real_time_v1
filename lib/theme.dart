import 'package:flutter/material.dart';

class AppTheme {
  static const Color darkBg = Color(0xFF0A0A0A);
  static const Color surface = Color(0xFF1A1A1A);
  static const Color accentNeon = Color(0xFF00FF9C);
  static const Color textBody = Color(0xFFE0E0E0);
  static const Color textDim = Color(0xFF888888);
  static const Color alertRed = Color(0xFFFF4D4D);

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBg,
      primaryColor: accentNeon,
      colorScheme: const ColorScheme.dark(
        primary: accentNeon,
        surface: surface,
        onSurface: textBody,
        secondary: accentNeon,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: darkBg,
        elevation: 0,
        titleTextStyle: TextStyle(
          color: accentNeon,
          fontSize: 20,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: surface,
        selectedItemColor: accentNeon,
        unselectedItemColor: textDim,
        type: BottomNavigationBarType.fixed,
      ),
      textTheme: const TextTheme(
        headlineMedium: TextStyle(
          color: accentNeon,
          fontSize: 24,
          fontWeight: FontWeight.bold,
        ),
        bodyLarge: TextStyle(color: textBody),
        bodyMedium: TextStyle(color: textBody),
      ),
    );
  }
}
