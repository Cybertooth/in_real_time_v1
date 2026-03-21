import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/story_item.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';

/// Phone calls — list view, tap to see wiretap transcript.
class PhoneCallScreen extends ConsumerWidget {
  const PhoneCallScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final callsAsync = ref.watch(phoneCallProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('CALL LOG')),
      body: callsAsync.when(
        data: (calls) {
          if (calls.isEmpty) {
            return const EmptyState(
              icon: Icons.phone_disabled,
              title: 'NO CALLS',
              subtitle: 'Intercepted phone calls will appear here.',
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: calls.length,
            itemBuilder: (_, i) => _CallCard(call: calls[i]),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

class _CallCard extends StatelessWidget {
  final PhoneCall call;
  const _CallCard({required this.call});

  String _formatDuration(int secs) {
    final m = secs ~/ 60;
    final s = secs % 60;
    return '${m}:${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => _showTranscript(context),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: AppTheme.cardDecoration(accentBorder: AppTheme.phoneCallColor),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: AppTheme.phoneCallColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Icon(Icons.phone, color: AppTheme.phoneCallColor, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${call.caller}  →  ${call.receiver}',
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Text('Duration: ${_formatDuration(call.durationSeconds)}', style: Theme.of(context).textTheme.bodySmall),
                      const SizedBox(width: 12),
                      Text('${call.lines.length} lines', style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                  const SizedBox(height: 2),
                  TimestampLabel(time: call.unlockTimestamp),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppTheme.textMuted, size: 20),
          ],
        ),
      ),
    );
  }

  void _showTranscript(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surfaceLow,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
      ),
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.85,
        expand: false,
        builder: (_, scrollCtrl) => _TranscriptSheet(call: call, scrollController: scrollCtrl),
      ),
    );
  }
}

class _TranscriptSheet extends StatelessWidget {
  final PhoneCall call;
  final ScrollController scrollController;
  const _TranscriptSheet({required this.call, required this.scrollController});

  String _formatDuration(int secs) {
    final m = secs ~/ 60;
    final s = secs % 60;
    return '${m}:${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: ListView(
        controller: scrollController,
        children: [
          // Header
          Row(
            children: [
              Text(
                'CALL TRANSCRIPT',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const Spacer(),
              const InterceptedLabel(),
            ],
          ),
          const SizedBox(height: 16),
          // Call info card
          Container(
            padding: const EdgeInsets.all(14),
            decoration: AppTheme.glassDecoration(),
            child: Row(
              children: [
                const Icon(Icons.phone, color: AppTheme.phoneCallColor, size: 18),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${call.caller}  →  ${call.receiver}',
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                      ),
                      Text(
                        'Duration: ${_formatDuration(call.durationSeconds)}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                TimestampLabel(time: call.unlockTimestamp),
              ],
            ),
          ),
          const SizedBox(height: 24),
          // Transcript lines
          ...call.lines.asMap().entries.map((entry) {
            final line = entry.value;
            final isCaller = line.speaker == call.caller;
            return Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 80,
                    child: Text(
                      line.speaker,
                      style: TextStyle(
                        color: isCaller ? AppTheme.phoneCallColor : AppTheme.accentSoft,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      line.text,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.5),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
