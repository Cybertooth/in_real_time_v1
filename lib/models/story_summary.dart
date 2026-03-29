import 'package:cloud_firestore/cloud_firestore.dart';

enum StoryLifecycleMode { live, scheduled, subscription }

enum StorySubscriptionSubMode { standard, onDemand }

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

StorySubscriptionSubMode _parseStorySubMode(Object? raw) {
  final value = (raw as String?)?.toLowerCase().trim();
  switch (value) {
    case 'on_demand':
    case 'ondemand':
      return StorySubscriptionSubMode.onDemand;
    case 'default':
    default:
      return StorySubscriptionSubMode.standard;
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
  final StorySubscriptionSubMode storySubMode;
  final DateTime? storyStartAt;
  final DateTime? storyEndAt;
  final int storyDurationMinutes;
  final String themeColorHex;
  final String ttsTier;
  final Map<String, String> voiceMap;
  final bool isPublished;
  final DateTime? publishedAt;
  final int onDemandBurstWindowMinutes;
  final int onDemandSessionDurationMinutes;
  final int onDemandInactivityResetMinutes;

  StorySummary({
    required this.id,
    required this.title,
    required this.createdAt,
    this.setup = '',
    this.tags = const [],
    this.characters = const [],
    this.headlineImageUrl,
    this.storyMode = StoryLifecycleMode.live,
    this.storySubMode = StorySubscriptionSubMode.standard,
    this.storyStartAt,
    this.storyEndAt,
    this.storyDurationMinutes = 0,
    this.themeColorHex = '#00FF9C',
    this.ttsTier = 'premium',
    this.voiceMap = const {},
    this.isPublished = true,
    this.publishedAt,
    this.onDemandBurstWindowMinutes = 90,
    this.onDemandSessionDurationMinutes = 9,
    this.onDemandInactivityResetMinutes = 12,
  });

  factory StorySummary.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final createdAt = _parseTimestamp(data['createdAt']) ?? DateTime.now();
    final startAt = _parseTimestamp(data['storyStartAt']);
    final endAt = _parseTimestamp(data['storyEndAt']);
    final publishedAt = _parseTimestamp(data['publishedAt']);
    final onDemandConfig = (data['onDemandConfig'] is Map<String, dynamic>)
        ? data['onDemandConfig'] as Map<String, dynamic>
        : const <String, dynamic>{};
    return StorySummary(
      id: doc.id,
      title: data['title'] ?? 'Untitled Story',
      createdAt: createdAt,
      setup: data['setup'] ?? '',
      tags: List<String>.from(data['tags'] ?? []),
      characters: List<Map<String, dynamic>>.from(data['characters'] ?? []),
      headlineImageUrl: data['headlineImageUrl'] as String?,
      storyMode: _parseStoryMode(data['storyMode']),
      storySubMode: _parseStorySubMode(data['storySubMode']),
      storyStartAt: startAt ?? createdAt,
      storyEndAt: endAt,
      storyDurationMinutes:
          (data['storyDurationMinutes'] as num?)?.toInt() ?? 0,
      themeColorHex: (data['themeColorHex'] as String?) ?? '#00FF9C',
      ttsTier: (data['ttsTier'] as String?) ?? 'premium',
      voiceMap: Map<String, String>.from(data['voiceMap'] ?? const {}),
      isPublished: (data['isPublished'] as bool?) ?? true,
      publishedAt: publishedAt,
      onDemandBurstWindowMinutes:
          (onDemandConfig['burstWindowMinutes'] as num?)?.toInt() ?? 90,
      onDemandSessionDurationMinutes:
          (onDemandConfig['sessionDurationMinutes'] as num?)?.toInt() ?? 9,
      onDemandInactivityResetMinutes:
          (onDemandConfig['inactivityResetMinutes'] as num?)?.toInt() ?? 12,
    );
  }

  bool get isSubscription => storyMode == StoryLifecycleMode.subscription;
  bool get isOnDemandSubscription =>
      isSubscription && storySubMode == StorySubscriptionSubMode.onDemand;

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
