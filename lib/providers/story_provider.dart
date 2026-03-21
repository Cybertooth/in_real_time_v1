import 'dart:async';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/story_item.dart';
import '../models/story_summary.dart';

// ---------------------------------------------------------------------------
// Platform helpers
// ---------------------------------------------------------------------------
bool get _isDesktop =>
    !kIsWeb &&
    (defaultTargetPlatform == TargetPlatform.windows ||
     defaultTargetPlatform == TargetPlatform.linux ||
     defaultTargetPlatform == TargetPlatform.macOS);

// ---------------------------------------------------------------------------
// Clock — ticks every minute to re-evaluate time gates
// ---------------------------------------------------------------------------
final clockProvider = StreamProvider<DateTime>((ref) {
  return Stream.periodic(const Duration(minutes: 1), (_) => DateTime.now());
});

// ---------------------------------------------------------------------------
// Firestore instance (null on desktop when Firebase is unavailable)
// ---------------------------------------------------------------------------
final firestoreProvider = Provider<FirebaseFirestore?>((ref) {
  if (_isDesktop) return null; // Firebase not initialised on desktop
  return FirebaseFirestore.instance;
});

// ---------------------------------------------------------------------------
// Dynamic Active Story ID Provider
// ---------------------------------------------------------------------------
final activeStoryIdProvider = StateNotifierProvider<ActiveStoryIdNotifier, String>((ref) {
  return ActiveStoryIdNotifier();
});

class ActiveStoryIdNotifier extends StateNotifier<String> {
  ActiveStoryIdNotifier() : super('story_latest') {
    _load();
  }

  static const _key = 'active_story_id';

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_key);
    if (saved != null && saved.isNotEmpty) {
      state = saved;
    }
  }

  Future<void> setStoryId(String id) async {
    state = id;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, id);
  }
}

// ---------------------------------------------------------------------------
// Provider to list all available stories
// ---------------------------------------------------------------------------
final allStoriesProvider = StreamProvider<List<StorySummary>>((ref) {
  final db = ref.watch(firestoreProvider);
  if (db == null) return Stream.value(<StorySummary>[]);

  return db
      .collection('stories')
      .orderBy('createdAt', descending: true)
      .snapshots()
      .map((snap) => snap.docs.map(StorySummary.fromFirestore).toList());
});

// ---------------------------------------------------------------------------
// Generic helper to create a Firestore stream provider for a collection
// ---------------------------------------------------------------------------
StreamProvider<List<T>> _collectionProvider<T extends StoryItem>(
  T Function(DocumentSnapshot) fromFirestore,
  String collectionName, {
  bool ascending = false,
}) {
  return StreamProvider<List<T>>((ref) {
    ref.watch(clockProvider);
    final db = ref.watch(firestoreProvider);
    final activeId = ref.watch(activeStoryIdProvider);
    
    if (db == null) return Stream.value(<T>[]);

    final now = DateTime.now();
    return db
        .collection('stories')
        .doc(activeId)
        .collection(collectionName)
        .where('unlockTimestamp', isLessThanOrEqualTo: Timestamp.fromDate(now))
        .orderBy('unlockTimestamp', descending: !ascending)
        .snapshots()
        .map((snap) => snap.docs.map(fromFirestore).toList());
  });
}

// ---------------------------------------------------------------------------
// Per‑type providers
// ---------------------------------------------------------------------------
final journalProvider =
    _collectionProvider<Journal>(Journal.fromFirestore, 'journals');

final chatProvider =
    _collectionProvider<Chat>(Chat.fromFirestore, 'chats', ascending: true);

final emailProvider =
    _collectionProvider<Email>(Email.fromFirestore, 'emails');

final receiptProvider =
    _collectionProvider<Receipt>(Receipt.fromFirestore, 'receipts');

final voiceNoteProvider =
    _collectionProvider<VoiceNote>(VoiceNote.fromFirestore, 'voice_notes');

final socialPostProvider =
    _collectionProvider<SocialPost>(SocialPost.fromFirestore, 'social_posts');

final phoneCallProvider =
    _collectionProvider<PhoneCall>(PhoneCall.fromFirestore, 'phone_calls');

final groupChatProvider =
    _collectionProvider<GroupChatThread>(GroupChatThread.fromFirestore, 'group_chats');

// ---------------------------------------------------------------------------
// Unified timeline — merges all content types into one sorted list
// ---------------------------------------------------------------------------
final timelineFeedProvider = Provider<AsyncValue<List<StoryItem>>>((ref) {
  final journals = ref.watch(journalProvider);
  final chats = ref.watch(chatProvider);
  final emails = ref.watch(emailProvider);
  final receipts = ref.watch(receiptProvider);
  final voiceNotes = ref.watch(voiceNoteProvider);
  final socialPosts = ref.watch(socialPostProvider);
  final phoneCalls = ref.watch(phoneCallProvider);
  final groupChats = ref.watch(groupChatProvider);

  // If any stream is still loading, show loading
  if (journals is AsyncLoading ||
      chats is AsyncLoading ||
      emails is AsyncLoading ||
      receipts is AsyncLoading ||
      voiceNotes is AsyncLoading ||
      socialPosts is AsyncLoading ||
      phoneCalls is AsyncLoading ||
      groupChats is AsyncLoading) {
    return const AsyncValue.loading();
  }

  // If any stream errored, propagate the first error
  for (final stream in [journals, chats, emails, receipts, voiceNotes, socialPosts, phoneCalls, groupChats]) {
    if (stream is AsyncError) {
      return AsyncValue.error(
        (stream as AsyncError).error,
        (stream as AsyncError).stackTrace,
      );
    }
  }

  final merged = <StoryItem>[
    ...journals.value ?? [],
    ...chats.value ?? [],
    ...emails.value ?? [],
    ...receipts.value ?? [],
    ...voiceNotes.value ?? [],
    ...socialPosts.value ?? [],
    ...phoneCalls.value ?? [],
    ...groupChats.value ?? [],
  ];

  merged.sort((a, b) => b.unlockTimestamp.compareTo(a.unlockTimestamp));
  return AsyncValue.data(merged);
});

// ---------------------------------------------------------------------------
// Upcoming items heuristic (are there locked items pending?)
// ---------------------------------------------------------------------------
final upcomingItemsProvider = StreamProvider<bool>((ref) {
  final db = ref.watch(firestoreProvider);
  final activeId = ref.watch(activeStoryIdProvider);
  
  if (db == null) return Stream.value(false);

  final now = DateTime.now();
  return db
      .collection('stories')
      .doc(activeId)
      .collection('journals')
      .where('unlockTimestamp', isGreaterThan: Timestamp.fromDate(now))
      .snapshots()
      .map((snap) => snap.docs.isNotEmpty);
});
