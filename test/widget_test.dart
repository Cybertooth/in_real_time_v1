// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:in_real_time_v1/main.dart';
import 'package:in_real_time_v1/providers/story_provider.dart';

void main() {
  testWidgets('App boots with navigation shell', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          firestoreProvider.overrideWithValue(null),
          clockProvider.overrideWith((ref) => Stream.value(DateTime.now())),
        ],
        child: InRealTimeApp(),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('Timeline'), findsOneWidget);
  });
}
