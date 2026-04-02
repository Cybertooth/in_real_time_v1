import '../models/story_item.dart';
import '../models/story_catchup_summary.dart';

/// Service for generating catch-up summaries from story items.
/// Uses deterministic heuristics to create recap content client-side.
class CatchUpGeneratorService {
  /// Generates a catch-up summary from a list of story items.
  /// 
  /// [storyId] - The ID of the story
  /// [items] - All items that have been unlocked since last session
  /// [since] - When the user last viewed the story
  /// [until] - Current time
  StoryCatchUpSummary generateSummary({
    required String storyId,
    required List<StoryItem> items,
    required DateTime since,
    required DateTime until,
  }) {
    if (items.isEmpty) {
      return StoryCatchUpSummary.empty(storyId);
    }

    // Sort chronologically
    final sortedItems = List<StoryItem>.from(items)
      ..sort((a, b) => a.unlockTimestamp.compareTo(b.unlockTimestamp));

    // Take first 8 items for analysis
    final analysisItems = sortedItems.take(8).toList();

    // Generate bullets and calculate weights
    final weightedItems = <_WeightedItem>[];
    for (final item in analysisItems) {
      final bullet = _generateBulletForItem(item);
      final weight = _calculateItemWeight(item, analysisItems);
      weightedItems.add(_WeightedItem(item: item, bullet: bullet, weight: weight));
    }

    // Sort by weight (highest first) and take top 3-4
    weightedItems.sort((a, b) => b.weight.compareTo(a.weight));
    final topItems = weightedItems.take(4).toList();
    
    // Sort back chronologically for display
    topItems.sort((a, b) => a.item.unlockTimestamp.compareTo(b.item.unlockTimestamp));

    final bullets = topItems.map((w) => w.bullet).where((b) => b.isNotEmpty).toList();

    // Generate headline
    final headline = _generateHeadline(sortedItems, topItems);

    // Generate unresolved question
    final unresolvedQuestion = _generateUnresolvedQuestion(sortedItems);

    // Get recommended resume item (highest weight item)
    final recommendedItemId = weightedItems.isNotEmpty ? weightedItems.first.item.id : null;

    // Count missed items by type
    final missedCountsByType = _countItemsByType(items);

    return StoryCatchUpSummary(
      storyId: storyId,
      since: since,
      until: until,
      headline: headline,
      bullets: bullets,
      unresolvedQuestion: unresolvedQuestion,
      recommendedResumeItemId: recommendedItemId,
      missedCountsByType: missedCountsByType,
    );
  }

  String _generateBulletForItem(StoryItem item) {
    return switch (item) {
      Journal j => _summarizeJournal(j),
      Chat c => '${c.senderId} messaged: "${_truncate(c.text, 40)}"',
      Email e => 'Email from ${e.sender}: "${_truncate(e.subject, 35)}"',
      Receipt r => 'Receipt: ${r.merchantName} - \$${r.amount.toStringAsFixed(2)}',
      VoiceNote v => 'Voice note from ${v.speaker}: "${_truncate(v.transcript, 40)}"',
      SocialPost s => 'Post from @${s.handle}: "${_truncate(s.content, 40)}"',
      PhoneCall p => 'Call between ${p.caller} and ${p.receiver}',
      GroupChatThread g => 'Group chat "${g.groupName}" escalated',
      GalleryPhoto gp => gp.caption != null && gp.caption!.isNotEmpty
          ? 'Photo: ${gp.caption}'
          : 'New photo: ${gp.subject}',
      _ => '',
    };
  }

  String _summarizeJournal(Journal journal) {
    if (journal.title.isNotEmpty) {
      return 'Journal entry: "${_truncate(journal.title, 40)}"';
    }
    return 'New journal entry discovered';
  }

  String _truncate(String text, int maxLength) {
    if (text.length <= maxLength) return text;
    return '${text.substring(0, maxLength)}...';
  }

  int _calculateItemWeight(StoryItem item, List<StoryItem> allItems) {
    int weight = 0;

    // Base weight by type
    weight += switch (item) {
      PhoneCall _ => 3,
      VoiceNote _ => 3,
      Receipt _ => 3,
      _ => 1,
    };

    // Bonus for media content
    if (item.imageUrl != null && item.imageUrl!.isNotEmpty) {
      weight += 2;
    }

    // Bonus for password-locked items (implies importance)
    if (item.isPasswordLocked) {
      weight += 2;
    }

    // Bonus for long journal entries with strong titles
    if (item is Journal) {
      if (item.title.length > 10) weight += 1;
      if (item.body.length > 200) weight += 1;
    }

    // Bonus for newest items
    final isNewest = allItems.isNotEmpty && 
        item.unlockTimestamp == allItems.last.unlockTimestamp;
    if (isNewest) weight += 1;

    return weight;
  }

  String _generateHeadline(List<StoryItem> allItems, List<_WeightedItem> topItems) {
    if (allItems.isEmpty) return 'Nothing new to report';

    final count = allItems.length;
    final hasSignificantEvents = topItems.any((w) => w.weight >= 3);

    if (hasSignificantEvents) {
      if (count == 1) return 'Something important happened';
      if (count <= 3) return 'Several developments to catch up on';
      return 'Major activity while you were away';
    }

    if (count == 1) return 'One new item since you left';
    if (count <= 5) return 'A few updates to review';
    return '$count new items to catch up on';
  }

  String _generateUnresolvedQuestion(List<StoryItem> items) {
    if (items.isEmpty) return 'What will happen next?';

    // Look for suspicious/recent items to base the question on
    final recentItems = items.reversed.take(3);
    
    for (final item in recentItems) {
      final question = switch (item) {
        PhoneCall p => 'What were ${p.caller} and ${p.receiver} discussing?',
        Receipt r when r.amount > 100 => 'Why the large transaction at ${r.merchantName}?',
        VoiceNote v => 'What is ${v.speaker} not saying directly?',
        Email e when e.subject.toLowerCase().contains('urgent') => 
            'What was so urgent in that email?',
        _ => null,
      };
      if (question != null) return question;
    }

    // Fallback questions
    final fallbacks = [
      'What are they hiding?',
      'Why did this happen now?',
      'Who else is involved?',
      'What will happen next?',
      'Is everything as it seems?',
    ];

    return fallbacks[items.length % fallbacks.length];
  }

  Map<String, int> _countItemsByType(List<StoryItem> items) {
    final counts = <String, int>{};
    for (final item in items) {
      counts[item.contentType] = (counts[item.contentType] ?? 0) + 1;
    }
    return counts;
  }
}

class _WeightedItem {
  final StoryItem item;
  final String bullet;
  final int weight;

  _WeightedItem({
    required this.item,
    required this.bullet,
    required this.weight,
  });
}
