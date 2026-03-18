import 'dart:async';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/story_item.dart';

// A clock that ticks every minute to trigger UI updates for time-gated content
final clockProvider = StreamProvider<DateTime>((ref) {
  return Stream.periodic(const Duration(minutes: 1), (_) => DateTime.now());
});

final firestoreProvider = Provider((ref) => FirebaseFirestore.instance);

// For simplicity, we assume there's only one "active" story.
// In a real app, you might fetch the latest story ID first.
const String activeStoryId = "story_latest"; // Placeholder

final journalProvider = StreamProvider<List<Journal>>((ref) {
  ref.watch(clockProvider); // Re-run query when clock ticks
  final now = DateTime.now();
  
  return ref.watch(firestoreProvider)
      .collection('stories')
      .doc(activeStoryId)
      .collection('journals')
      .where('unlockTimestamp', isLessThanOrEqualTo: Timestamp.fromDate(now))
      .orderBy('unlockTimestamp', descending: true)
      .snapshots()
      .map((snapshot) => snapshot.docs.map(Journal.fromFirestore).toList());
});

final chatProvider = StreamProvider<List<Chat>>((ref) {
  ref.watch(clockProvider);
  final now = DateTime.now();
  
  return ref.watch(firestoreProvider)
      .collection('stories')
      .doc(activeStoryId)
      .collection('chats')
      .where('unlockTimestamp', isLessThanOrEqualTo: Timestamp.fromDate(now))
      .orderBy('unlockTimestamp', descending: false) // Chats usually chronological
      .snapshots()
      .map((snapshot) => snapshot.docs.map(Chat.fromFirestore).toList());
});

final emailProvider = StreamProvider<List<Email>>((ref) {
  ref.watch(clockProvider);
  final now = DateTime.now();
  
  return ref.watch(firestoreProvider)
      .collection('stories')
      .doc(activeStoryId)
      .collection('emails')
      .where('unlockTimestamp', isLessThanOrEqualTo: Timestamp.fromDate(now))
      .orderBy('unlockTimestamp', descending: true)
      .snapshots()
      .map((snapshot) => snapshot.docs.map(Email.fromFirestore).toList());
});

final receiptProvider = StreamProvider<List<Receipt>>((ref) {
  ref.watch(clockProvider);
  final now = DateTime.now();
  
  return ref.watch(firestoreProvider)
      .collection('stories')
      .doc(activeStoryId)
      .collection('receipts')
      .where('unlockTimestamp', isLessThanOrEqualTo: Timestamp.fromDate(now))
      .orderBy('unlockTimestamp', descending: true)
      .snapshots()
      .map((snapshot) => snapshot.docs.map(Receipt.fromFirestore).toList());
});

// Provider to check for ANY upcoming items (for showing 'Locked' state in UI)
final upcomingItemsProvider = StreamProvider<bool>((ref) {
  final now = DateTime.now();
  return ref.watch(firestoreProvider)
      .collection('stories')
      .doc(activeStoryId)
      .collection('journals') // Just check journals for now as a heuristic
      .where('unlockTimestamp', isGreaterThan: Timestamp.fromDate(now))
      .snapshots()
      .map((snapshot) => snapshot.docs.isNotEmpty);
});
