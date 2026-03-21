import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../models/story_item.dart';
import '../widgets/shared_widgets.dart';

class JournalScreen extends ConsumerWidget {
  const JournalScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final journalsAsync = ref.watch(journalProvider);
    final hasUpcoming = ref.watch(upcomingItemsProvider).value ?? false;

    return Scaffold(
      appBar: AppBar(title: const Text('JOURNAL')),
      body: journalsAsync.when(
        data: (journals) {
          if (journals.isEmpty && !hasUpcoming) {
            return const EmptyState(
              icon: Icons.auto_stories,
              title: 'NO ENTRIES',
              subtitle: 'Journal entries will appear here as they are intercepted.',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: journals.length + (hasUpcoming ? 1 : 0),
            itemBuilder: (context, index) {
              if (index == 0 && hasUpcoming) {
                return _buildLockedEntry(context);
              }
              final journal = journals[hasUpcoming ? index - 1 : index];
              return _buildJournalCard(context, journal);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildLockedEntry(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(24),
      decoration: AppTheme.glassDecoration(),
      child: Column(
        children: [
          const Icon(Icons.lock_outline, color: AppTheme.textMuted, size: 28),
          const SizedBox(height: 12),
          Text(
            'ENCRYPTED_FILE_LOCKED',
            style: TextStyle(
              color: AppTheme.textMuted,
              fontFamily: 'monospace',
              fontSize: 12,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Waiting for next synchronization event…',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  Widget _buildJournalCard(BuildContext context, Journal journal) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.cardDecoration(accentBorder: AppTheme.journalColor),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const TypeBadge(label: 'Journal', color: AppTheme.journalColor, icon: Icons.auto_stories),
              const Spacer(),
              TimestampLabel(time: journal.unlockTimestamp),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            journal.title.toUpperCase(),
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: AppTheme.accentNeon,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            journal.body,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ],
      ),
    );
  }
}
