import 'package:cloud_firestore/cloud_firestore.dart';

class StorySummary {
  final String id;
  final String title;
  final DateTime createdAt;
  final String setup;
  final List<String> tags;
  final List<Map<String, dynamic>> characters;
  final String? headlineImageUrl;

  StorySummary({
    required this.id,
    required this.title,
    required this.createdAt,
    this.setup = '',
    this.tags = const [],
    this.characters = const [],
    this.headlineImageUrl,
  });

  factory StorySummary.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return StorySummary(
      id: doc.id,
      title: data['title'] ?? 'Untitled Story',
      createdAt: (data['createdAt'] as Timestamp).toDate(),
      setup: data['setup'] ?? '',
      tags: List<String>.from(data['tags'] ?? []),
      characters: List<Map<String, dynamic>>.from(data['characters'] ?? []),
      headlineImageUrl: data['headlineImageUrl'] as String?,
    );
  }
}
