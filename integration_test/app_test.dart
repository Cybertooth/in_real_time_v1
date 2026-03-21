import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:in_real_time_v1/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('End-to-End Test', () {
    testWidgets('Full flow: Home -> Gallery -> Select Story -> Timeline', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      // 1. Verify we are on Timeline (Home)
      expect(find.text('Timeline'), findsWidgets);

      // 2. Navigate to Gallery
      final galleryTab = find.byIcon(Icons.history_edu_outlined);
      await tester.tap(galleryTab);
      await tester.pumpAndSettle();

      expect(find.text('Story Gallery'), findsOneWidget);

      // 3. Select a story (This assumes there's at least one story in Firestore)
      // Since we are running against real Firestore (E2E), we'll try to find a story.
      // If none, the test might fail or we can just verify the "No stories found" message.
      final storyItem = find.byType(InkWell).first; // Pick the first story if available
      if (tester.any(storyItem)) {
        await tester.tap(storyItem);
        await tester.pumpAndSettle();

        // Verify SnackBar or navigation back
        expect(find.byType(SnackBar), findsOneWidget);

        // 4. Go back to Timeline
        final timelineTab = find.byIcon(Icons.timeline_outlined);
        await tester.tap(timelineTab);
        await tester.pumpAndSettle();
        
        expect(find.text('Timeline'), findsWidgets);
      } else {
        expect(find.text('No stories found in Firestore.'), findsOneWidget);
      }

      // 5. Navigate to Settings
      final settingsTab = find.byIcon(Icons.settings_outlined);
      await tester.tap(settingsTab);
      await tester.pumpAndSettle();

      expect(find.text('Settings'), findsOneWidget);
      expect(find.text('Backend URL'), findsOneWidget);
    });
  });
}
