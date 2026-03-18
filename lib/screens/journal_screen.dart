import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../models/story_item.dart';

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
            return const Center(child: Text('No journal entries found.'));
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: journals.length + (hasUpcoming ? 1 : 0),
            itemBuilder: (context, index) {
              if (index == 0 && hasUpcoming) {
                return _buildLockedEntry();
              }
              final journal = journals[hasUpcoming ? index - 1 : index];
              return _buildJournalCard(journal);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildLockedEntry() {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        border: Border.all(color: AppTheme.textDim, width: 0.5),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          const Icon(Icons.lock_outline, color: AppTheme.textDim, size: 32),
          const SizedBox(height: 12),
          Text(
            'ENCRYPTED_FILE_LOCKED',
            style: TextStyle(
              color: AppTheme.textDim,
              fontFamily: 'Courier',
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Waiting for next synchronization event...',
            style: TextStyle(color: AppTheme.textDim, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildJournalCard(Journal journal) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        border: Border.all(color: AppTheme.accentNeon, width: 0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            journal.title.toUpperCase(),
            style: const TextStyle(
              color: AppTheme.accentNeon,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            DateFormat('yyyy-MM-dd HH:mm').format(journal.unlockTimestamp),
            style: const TextStyle(color: AppTheme.textDim, fontSize: 12),
          ),
          const Divider(color: AppTheme.accentNeon, thickness: 0.3, height: 24),
          Text(
            journal.body,
            style: const TextStyle(height: 1.5),
          ),
        ],
      ),
    );
  }
}
