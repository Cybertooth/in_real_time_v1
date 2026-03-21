import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:in_real_time_v1/screens/story_gallery_screen.dart';
import 'package:in_real_time_v1/providers/story_provider.dart';
import 'package:in_real_time_v1/models/story_summary.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('StoryGalleryScreen shows stories and allows selection', (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});

    // Mock stories
    final mockStories = [
      StorySummary(id: 'story_1', title: 'First Story', createdAt: DateTime.now()),
      StorySummary(id: 'story_2', title: 'Second Story', createdAt: DateTime.now().subtract(const Duration(days: 1))),
    ];

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          // Override allStoriesProvider to return our mock data
          allStoriesProvider.overrideWith((ref) => Stream.value(mockStories)),
        ],
        child: const MaterialApp(
          home: StoryGalleryScreen(),
        ),
      ),
    );

    // Initial pump to show loading or empty
    await tester.pump();
    // Pump again to process the stream
    await tester.pump(Duration.zero);

    // Verify stories are displayed
    expect(find.text('First Story'), findsOneWidget);
    expect(find.text('Second Story'), findsOneWidget);

    // Tap on the second story
    await tester.tap(find.text('Second Story'));
    await tester.pumpAndSettle();

    // The ActiveStoryIdNotifier should have been updated. 
    // We can verify this by checking the provider state in the scope.
    final container = ProviderScope.containerOf(tester.element(find.byType(StoryGalleryScreen)));
    expect(container.read(activeStoryIdProvider), 'story_2');
    
    // Verify SnackBar shown
    expect(find.text('Switched to: Second Story'), findsOneWidget);
  });
}
