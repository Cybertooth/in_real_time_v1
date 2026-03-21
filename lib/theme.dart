import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// "Ghost Signal" design system — adapted from Stitch.
///
/// Surface hierarchy (tonal layering, no divider lines):
///   Level 0  surface         #0e0e0e   — deep background / scaffold
///   Level 1  surfaceLow      #131313   — large structural areas
///   Level 2  surface (card)  #1A1A1A   — primary interactive surface
///   Level 3  surfaceHigh     #262626   — popovers, active cards
class AppTheme {
  // ── Palette ──────────────────────────────────────────────────────────────
  static const Color darkBg = Color(0xFF0E0E0E);
  static const Color surface = Color(0xFF1A1A1A);
  static const Color surfaceLow = Color(0xFF131313);
  static const Color surfaceHigh = Color(0xFF262626);
  static const Color surfaceBright = Color(0xFF2C2C2C);

  static const Color accentNeon = Color(0xFF00FF9C); // primary mint
  static const Color accentSoft = Color(0xFFA1FFC2); // primary light
  static const Color secondary = Color(0xFF65F9C3);
  static const Color tertiary = Color(0xFF77DFFF); // ice‑blue accent

  static const Color textBody = Color(0xFFE0E0E0);
  static const Color textDim = Color(0xFFADAAAa);
  static const Color textMuted = Color(0xFF777575);

  static const Color alertRed = Color(0xFFFF716C);
  static const Color alertAmber = Color(0xFFFFB74D);

  // ── Per‑content‑type accent colours ─────────────────────────────────────
  static const Color journalColor = accentNeon;
  static const Color chatColor = accentSoft;
  static const Color emailColor = Color(0xFF90CAF9);
  static const Color receiptColor = accentNeon;
  static const Color voiceNoteColor = Color(0xFFCE93D8);
  static const Color socialPostColor = Color(0xFFFF8A65);
  static const Color phoneCallColor = tertiary;
  static const Color groupChatColor = Color(0xFFAED581);

  // ── Reusable card decoration ────────────────────────────────────────────
  static BoxDecoration cardDecoration({
    Color? accentBorder,
    bool glow = false,
  }) {
    return BoxDecoration(
      color: surface,
      borderRadius: BorderRadius.circular(4),
      border: accentBorder != null
          ? Border(left: BorderSide(color: accentBorder, width: 3))
          : Border.all(color: Colors.white.withOpacity(0.04)),
      boxShadow: glow
          ? [BoxShadow(color: accentNeon.withOpacity(0.12), blurRadius: 12)]
          : null,
    );
  }

  static BoxDecoration glassDecoration({double opacity = 0.06}) {
    return BoxDecoration(
      color: Colors.white.withOpacity(opacity),
      borderRadius: BorderRadius.circular(4),
      border: Border.all(color: Colors.white.withOpacity(0.04)),
    );
  }

  // ── Theme Data ──────────────────────────────────────────────────────────
  static ThemeData get darkTheme {
    final headline = GoogleFonts.spaceGrotesk();
    final body = GoogleFonts.manrope();

    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBg,
      primaryColor: accentNeon,
      colorScheme: const ColorScheme.dark(
        primary: accentNeon,
        secondary: secondary,
        tertiary: tertiary,
        surface: surface,
        onSurface: textBody,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: darkBg,
        elevation: 0,
        scrolledUnderElevation: 0,
        titleTextStyle: headline.copyWith(
          color: accentNeon,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.8,
        ),
        iconTheme: const IconThemeData(color: textDim),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: surfaceLow,
        selectedItemColor: accentNeon,
        unselectedItemColor: textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 0.8),
        unselectedLabelStyle: TextStyle(fontSize: 10, letterSpacing: 0.6),
      ),
      textTheme: TextTheme(
        displayLarge: headline.copyWith(color: accentNeon, fontSize: 28, fontWeight: FontWeight.bold),
        headlineMedium: headline.copyWith(color: accentNeon, fontSize: 20, fontWeight: FontWeight.w600),
        headlineSmall: headline.copyWith(color: textBody, fontSize: 16, fontWeight: FontWeight.w600),
        titleMedium: headline.copyWith(color: textBody, fontSize: 14, fontWeight: FontWeight.w500),
        bodyLarge: body.copyWith(color: textBody, fontSize: 15, height: 1.6),
        bodyMedium: body.copyWith(color: textBody, fontSize: 14, height: 1.5),
        bodySmall: body.copyWith(color: textDim, fontSize: 12),
        labelSmall: headline.copyWith(color: textDim, fontSize: 10, fontWeight: FontWeight.w500, letterSpacing: 1.2),
        labelMedium: headline.copyWith(color: textDim, fontSize: 12, fontWeight: FontWeight.w500),
      ),
      dividerTheme: DividerThemeData(color: Colors.white.withOpacity(0.04), thickness: 1, space: 0),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(4),
          side: BorderSide(color: Colors.white.withOpacity(0.04)),
        ),
      ),
    );
  }
}
