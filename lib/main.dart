import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/story_provider.dart';
import 'screens/main_navigation.dart';
import 'theme.dart';

// Conditionally import Firebase packages — they are available but we only
// initialise on mobile platforms where google-services.json is present.
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

/// Whether the app is running on a desktop OS (Windows/macOS/Linux).
bool get _isDesktop =>
    !kIsWeb &&
    (defaultTargetPlatform == TargetPlatform.windows ||
     defaultTargetPlatform == TargetPlatform.linux ||
     defaultTargetPlatform == TargetPlatform.macOS);

// Background message handler (mobile only).
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Firebase is only available on mobile (Android/iOS) where google-services.json
  // or GoogleService-Info.plist exists. On desktop we skip initialisation entirely
  // so the app can render the UI with empty data providers.
  if (!_isDesktop) {
    try {
      await Firebase.initializeApp();

      FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

      final messaging = FirebaseMessaging.instance;
      await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );
    } catch (e) {
      debugPrint('[InRealTime] Firebase init skipped or failed: $e');
    }
  } else {
    debugPrint('[InRealTime] Running on desktop — Firebase disabled, using empty providers.');
  }

  runApp(
    const ProviderScope(
      child: InRealTimeApp(),
    ),
  );
}

class InRealTimeApp extends ConsumerWidget {
  const InRealTimeApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final accent = ref.watch(activeStoryThemeColorProvider);
    return MaterialApp(
      title: 'In Real Time',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.themedDarkTheme(accent),
      home: const MainNavigation(),
    );
  }
}
