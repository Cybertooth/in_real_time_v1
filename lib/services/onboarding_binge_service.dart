import 'package:shared_preferences/shared_preferences.dart';

/// Service for managing onboarding binge-to-live state per story.
/// Tracks whether a user is currently in binge mode for a story and
/// manages the transition to live mode.
class OnboardingBingeService {
  static const _bingeStartedPrefix = 'story_binge_started_';
  static const _bingeCompletedPrefix = 'story_binge_completed_';
  static const _bingeLastSeenItemPrefix = 'story_binge_last_seen_';
  static const _bingeProgressPrefix = 'story_binge_progress_';
  static const _bingeSeenItemsPrefix = 'story_binge_seen_items_';

  static const int defaultBingeArtifactCount = 12;

  /// Checks if binge mode is available for a story.
  /// Returns true if the user hasn't started or completed binge for this story.
  Future<bool> isBingeAvailable(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    final completed = prefs.getBool('$_bingeCompletedPrefix$storyId') ?? false;
    return !completed;
  }

  /// Checks if the user is currently in an active binge session for a story.
  Future<bool> isBingeActive(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    final started = prefs.getBool('$_bingeStartedPrefix$storyId') ?? false;
    final completed = prefs.getBool('$_bingeCompletedPrefix$storyId') ?? false;
    return started && !completed;
  }

  /// Starts a binge session for a story.
  Future<void> startBinge(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('$_bingeStartedPrefix$storyId', true);
    await prefs.remove('$_bingeCompletedPrefix$storyId');
    await prefs.setInt('$_bingeProgressPrefix$storyId', 0);
    await prefs.setStringList('$_bingeSeenItemsPrefix$storyId', <String>[]);
  }

  /// Marks a binge as completed for a story.
  Future<void> completeBinge(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('$_bingeCompletedPrefix$storyId', true);
  }

  /// Updates the binge progress (number of items viewed).
  Future<void> updateBingeProgress(String storyId, int itemsViewed) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('$_bingeProgressPrefix$storyId', itemsViewed);
    await prefs.setString(
      '$_bingeLastSeenItemPrefix$storyId',
      DateTime.now().toIso8601String(),
    );
  }

  /// Gets the current binge progress (number of items viewed).
  Future<int> getBingeProgress(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    final seenItems = prefs.getStringList('$_bingeSeenItemsPrefix$storyId');
    if (seenItems != null) {
      return seenItems.length;
    }
    return prefs.getInt('$_bingeProgressPrefix$storyId') ?? 0;
  }

  /// Records a newly viewed binge item and returns true only when
  /// the item had not already been counted.
  Future<bool> recordViewedItem(String storyId, String itemId) async {
    final prefs = await SharedPreferences.getInstance();
    final key = '$_bingeSeenItemsPrefix$storyId';
    final seenItems = List<String>.from(prefs.getStringList(key) ?? const []);
    if (seenItems.contains(itemId)) {
      return false;
    }

    seenItems.add(itemId);
    await prefs.setStringList(key, seenItems);
    await prefs.setInt('$_bingeProgressPrefix$storyId', seenItems.length);
    await prefs.setString(
      '$_bingeLastSeenItemPrefix$storyId',
      DateTime.now().toIso8601String(),
    );
    return true;
  }

  /// Checks if the user has reached the binge boundary.
  Future<bool> hasReachedBingeBoundary(
    String storyId, {
    int boundaryCount = defaultBingeArtifactCount,
  }) async {
    final progress = await getBingeProgress(storyId);
    return progress >= boundaryCount;
  }

  /// Gets the last seen item timestamp during binge.
  Future<DateTime?> getBingeLastSeenAt(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    final isoString = prefs.getString('$_bingeLastSeenItemPrefix$storyId');
    if (isoString == null) return null;
    return DateTime.tryParse(isoString);
  }

  /// Resets binge state for a story (useful for testing).
  Future<void> resetBingeState(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('$_bingeStartedPrefix$storyId');
    await prefs.remove('$_bingeCompletedPrefix$storyId');
    await prefs.remove('$_bingeLastSeenItemPrefix$storyId');
    await prefs.remove('$_bingeProgressPrefix$storyId');
    await prefs.remove('$_bingeSeenItemsPrefix$storyId');
  }

  /// Checks if an item should be unlocked during binge mode.
  /// Items are unlocked if their index is within the binge boundary.
  bool isItemUnlockedByBinge({
    required int itemIndex,
    required int bingeProgress,
    int boundaryCount = defaultBingeArtifactCount,
  }) {
    // During binge, unlock items up to the boundary
    return itemIndex < boundaryCount;
  }

  /// Determines if binge mode should be enabled for a story.
  /// Currently checks story metadata - can be extended to check
  /// story-specific configuration from backend.
  bool shouldEnableBingeForStory({
    required bool onboardingBingeEnabled,
    required int totalArtifactCount,
    int minimumArtifactsRequired = 5,
  }) {
    // Don't enable binge if explicitly disabled
    if (!onboardingBingeEnabled) return false;
    
    // Don't enable if story has too few artifacts
    if (totalArtifactCount < minimumArtifactsRequired) return false;
    
    return true;
  }
}
