/// Model representing a catch-up summary for returning users.
/// Generated client-side from unlocked story items.
class StoryCatchUpSummary {
  final String storyId;
  final DateTime since;
  final DateTime until;
  final String headline;
  final List<String> bullets;
  final String unresolvedQuestion;
  final String? recommendedResumeItemId;
  final Map<String, int> missedCountsByType;

  const StoryCatchUpSummary({
    required this.storyId,
    required this.since,
    required this.until,
    required this.headline,
    required this.bullets,
    required this.unresolvedQuestion,
    this.recommendedResumeItemId,
    required this.missedCountsByType,
  });

  /// Creates an empty summary for when no catch-up is needed.
  factory StoryCatchUpSummary.empty(String storyId) {
    return StoryCatchUpSummary(
      storyId: storyId,
      since: DateTime.now(),
      until: DateTime.now(),
      headline: '',
      bullets: [],
      unresolvedQuestion: '',
      missedCountsByType: {},
    );
  }

  /// Gets the total number of missed artifacts.
  int get totalMissed {
    return missedCountsByType.values.fold(0, (sum, count) => sum + count);
  }

  /// Gets a human-readable summary of missed content types.
  String get missedSummary {
    if (missedCountsByType.isEmpty) return 'No new content';
    
    final parts = <String>[];
    missedCountsByType.forEach((type, count) {
      final label = _pluralizeType(type, count);
      parts.add('$count $label');
    });
    
    if (parts.length == 1) return parts.first;
    if (parts.length == 2) return '${parts.first} and ${parts.last}';
    
    final allButLast = parts.take(parts.length - 1).join(', ');
    return '$allButLast, and ${parts.last}';
  }

  String _pluralizeType(String type, int count) {
    final singular = _typeDisplayNames[type] ?? type;
    if (count == 1) return singular;
    
    // Simple pluralization
    if (singular.endsWith('s')) return '${singular}es';
    return '${singular}s';
  }

  static const _typeDisplayNames = {
    'journal': 'Journal',
    'chat': 'Chat',
    'email': 'Email',
    'receipt': 'Receipt',
    'voice_note': 'Voice Note',
    'social_post': 'Post',
    'phone_call': 'Call',
    'group_chat': 'Group Chat',
    'gallery_photo': 'Photo',
  };

  /// Gets display name for a content type.
  static String getDisplayNameForType(String type) {
    return _typeDisplayNames[type] ?? type;
  }
}
