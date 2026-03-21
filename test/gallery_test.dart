import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:in_real_time_v1/providers/story_provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('ActiveStoryIdNotifier Tests', () {
    late ProviderContainer container;

    setUp(() async {
      SharedPreferences.setMockInitialValues({});
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('Initial state is story_latest', () {
      final activeId = container.read(activeStoryIdProvider);
      expect(activeId, 'story_latest');
    });

    test('updates state and persists to SharedPreferences', () async {
      const newId = 'story_123456';
      
      // Update state
      await container.read(activeStoryIdProvider.notifier).setStoryId(newId);
      
      // Check state
      expect(container.read(activeStoryIdProvider), newId);
      
      // Check persistence
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('active_story_id'), newId);
    });

    test('loads persisted state on initialisation', () async {
      const savedId = 'story_saved';
      SharedPreferences.setMockInitialValues({'active_story_id': savedId});
      
      final newContainer = ProviderContainer();
      
      // Trigger the provider creation
      newContainer.read(activeStoryIdProvider);
      
      // Wait for _load() to complete
      await Future.delayed(const Duration(milliseconds: 200));
      
      expect(newContainer.read(activeStoryIdProvider), savedId);
      newContainer.dispose();
    });
  });
}
