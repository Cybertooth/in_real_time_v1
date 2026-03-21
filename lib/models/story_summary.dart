import 'package:cloud_firestore/cloud_firestore.dart';

class StorySummary {
  final String id;
  final String title;
  final DateTime createdAt;

  StorySummary({
    required this.id,
    required this.title,
    required this.createdAt,
  });

  factory StorySummary.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return StorySummary(
      id: doc.id,
      title: data['title'] ?? 'Untitled Story',
      createdAt: (data['createdAt'] as Timestamp).toDate(),
    );
  }
}
