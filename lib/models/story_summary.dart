import 'package:cloud_firestore/cloud_firestore.dart';

enum StoryLifecycleMode { live, scheduled, subscription }

StoryLifecycleMode _parseStoryMode(Object? raw) {
  final value = (raw as String?)?.toLowerCase().trim();
  switch (value) {
    case 'scheduled':
      return StoryLifecycleMode.scheduled;
    case 'subscription':
      return StoryLifecycleMode.subscription;
    case 'live':
    default:
      return StoryLifecycleMode.live;
  }
}

DateTime? _parseTimestamp(Object? raw) {
  if (raw is Timestamp) return raw.toDate();
  if (raw is DateTime) return raw;
  return null;
}

class StorySummary {
  final String id;
  final String title;
  final DateTime createdAt;
  final String setup;
  final List<String> tags;
  final List<Map<String, dynamic>> characters;
  final String? headlineImageUrl;
  final StoryLifecycleMode storyMode;
  final DateTime? storyStartAt;
  final DateTime? storyEndAt;
  final int storyDurationMinutes;
  final String themeColorHex;
  final String ttsTier;
  final Map<String, String> voiceMap;

  StorySummary({
    required this.id,
    required this.title,
    required this.createdAt,
    this.setup = '',
    this.tags = const [],
    this.characters = const [],
    this.headlineImageUrl,
    this.storyMode = StoryLifecycleMode.live,
    this.storyStartAt,
    this.storyEndAt,
    this.storyDurationMinutes = 0,
    this.themeColorHex = '#00FF9C',
    this.ttsTier = 'premium',
    this.voiceMap = const {},
  });

  factory StorySummary.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final createdAt = _parseTimestamp(data['createdAt']) ?? DateTime.now();
    final startAt = _parseTimestamp(data['storyStartAt']);
    final endAt = _parseTimestamp(data['storyEndAt']);
    return StorySummary(
      id: doc.id,
      title: data['title'] ?? 'Untitled Story',
      createdAt: createdAt,
      setup: data['setup'] ?? '',
      tags: List<String>.from(data['tags'] ?? []),
      characters: List<Map<String, dynamic>>.from(data['characters'] ?? []),
      headlineImageUrl: data['headlineImageUrl'] as String?,
      storyMode: _parseStoryMode(data['storyMode']),
      storyStartAt: startAt ?? createdAt,
      storyEndAt: endAt,
      storyDurationMinutes: (data['storyDurationMinutes'] as num?)?.toInt() ?? 0,
      themeColorHex: (data['themeColorHex'] as String?) ?? '#00FF9C',
      ttsTier: (data['ttsTier'] as String?) ?? 'premium',
      voiceMap: Map<String, String>.from(data['voiceMap'] ?? const {}),
    );
  }

  bool get isSubscription => storyMode == StoryLifecycleMode.subscription;

  bool get isUpcoming {
    if (storyMode != StoryLifecycleMode.scheduled) return false;
    final start = storyStartAt;
    if (start == null) return false;
    return start.isAfter(DateTime.now());
  }

  bool get isLiveNow {
    if (storyMode != StoryLifecycleMode.live) return false;
    final now = DateTime.now();
    final start = storyStartAt ?? createdAt;
    if (now.isBefore(start)) return false;
    if (storyDurationMinutes <= 0) return true;
    return now.isBefore(start.add(Duration(minutes: storyDurationMinutes)));
  }

  int get liveCompletionPercent {
    if (storyMode != StoryLifecycleMode.live) return 0;
    final start = storyStartAt ?? createdAt;
    final duration = storyDurationMinutes <= 0 ? 1 : storyDurationMinutes;
    final elapsed = DateTime.now().difference(start).inMinutes;
    if (elapsed <= 0) return 0;
    if (elapsed >= duration) return 100;
    return ((elapsed / duration) * 100).clamp(0, 100).round();
  }
}
