import 'dart:async';
import 'package:shared_preferences/shared_preferences.dart';

/// Service for managing user story resume state and checkpoints.
/// Tracks per-story "last seen" position for catch-up functionality.
class StoryResumeService {
  static const _lastSeenAtPrefix = 'story_last_seen_at_';
  static const _lastSeenItemIdPrefix = 'story_last_seen_item_id_';
  static const _lastCatchUpSeenAtPrefix = 'story_last_catchup_seen_at_';
  static const _catchUpDismissedPrefix = 'story_catchup_dismissed_session_';

  /// Records that a user has seen a specific story item.
  /// Call this when the user opens an item detail screen.
  Future<void> markItemAsSeen({
    required String storyId,
    required String itemId,
    DateTime? seenAt,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final timestamp = seenAt ?? DateTime.now();
    
    await prefs.setString(
      '$_lastSeenAtPrefix$storyId',
      timestamp.toIso8601String(),
    );
    await prefs.setString('$_lastSeenItemIdPrefix$storyId', itemId);
  }

  /// Gets the timestamp when the user last viewed any item in the story.
  Future<DateTime?> getLastSeenAt(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    final isoString = prefs.getString('$_lastSeenAtPrefix$storyId');
    if (isoString == null) return null;
    return DateTime.tryParse(isoString);
  }

  /// Gets the ID of the last item the user viewed.
  Future<String?> getLastSeenItemId(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('$_lastSeenItemIdPrefix$storyId');
  }

  /// Checks if the user has ever opened this story before.
  Future<bool> hasPreviouslyOpenedStory(String storyId) async {
    final lastSeen = await getLastSeenAt(storyId);
    return lastSeen != null;
  }

  /// Records when the catch-up capsule was last shown to the user.
  Future<void> markCatchUpSeen(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      '$_lastCatchUpSeenAtPrefix$storyId',
      DateTime.now().toIso8601String(),
    );
  }

  /// Gets when the catch-up capsule was last shown.
  Future<DateTime?> getLastCatchUpSeenAt(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    final isoString = prefs.getString('$_lastCatchUpSeenAtPrefix$storyId');
    if (isoString == null) return null;
    return DateTime.tryParse(isoString);
  }

  /// Dismisses the catch-up capsule for the current app session.
  Future<void> dismissCatchUpForSession(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('$_catchUpDismissedPrefix$storyId', true);
  }

  /// Checks if the catch-up capsule has been dismissed for this session.
  Future<bool> isCatchUpDismissedForSession(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool('$_catchUpDismissedPrefix$storyId') ?? false;
  }

  /// Clears the session dismissal flag (call on app startup).
  Future<void> clearSessionDismissals() async {
    final prefs = await SharedPreferences.getInstance();
    final keys = prefs.getKeys();
    for (final key in keys) {
      if (key.startsWith(_catchUpDismissedPrefix)) {
        await prefs.remove(key);
      }
    }
  }

  /// Determines if a catch-up capsule should be shown.
  /// 
  /// Rules:
  /// - User must have previously opened this story
  /// - User must have been away for at least [minAwayDuration]
  /// - There must be at least [minNewArtifacts] new unlocked items since last seen
  /// - Catch-up must not have been dismissed for this session
  Future<bool> shouldShowCatchUp({
    required String storyId,
    required DateTime now,
    required int newArtifactsCount,
    Duration minAwayDuration = const Duration(hours: 6),
    int minNewArtifacts = 3,
  }) async {
    // Don't show if dismissed for this session
    if (await isCatchUpDismissedForSession(storyId)) {
      return false;
    }

    // Don't show for first-time story sessions
    final lastSeenAt = await getLastSeenAt(storyId);
    if (lastSeenAt == null) {
      return false;
    }

    // Check if user has been away long enough
    final timeAway = now.difference(lastSeenAt);
    if (timeAway < minAwayDuration) {
      return false;
    }

    // Check if there's enough new content
    if (newArtifactsCount < minNewArtifacts) {
      return false;
    }

    return true;
  }

  /// Resets all resume state for a story (useful for testing).
  Future<void> resetStoryState(String storyId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('$_lastSeenAtPrefix$storyId');
    await prefs.remove('$_lastSeenItemIdPrefix$storyId');
    await prefs.remove('$_lastCatchUpSeenAtPrefix$storyId');
    await prefs.remove('$_catchUpDismissedPrefix$storyId');
  }
}
