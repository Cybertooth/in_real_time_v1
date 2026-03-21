import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/story_item.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';

/// Full-screen list of intercepted voice memos.
class VoiceNoteScreen extends ConsumerWidget {
  const VoiceNoteScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notesAsync = ref.watch(voiceNoteProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('VOICE NOTES')),
      body: notesAsync.when(
        data: (notes) {
          if (notes.isEmpty) {
            return const EmptyState(
              icon: Icons.mic_off,
              title: 'NO RECORDINGS',
              subtitle: 'Intercepted voice recordings will appear here.',
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: notes.length,
            itemBuilder: (_, i) => _VoiceNoteDetailCard(note: notes[i], isFirst: i == 0),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

class _VoiceNoteDetailCard extends StatelessWidget {
  final VoiceNote note;
  final bool isFirst;
  const _VoiceNoteDetailCard({required this.note, this.isFirst = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.cardDecoration(
        accentBorder: AppTheme.voiceNoteColor,
        glow: isFirst,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: AppTheme.voiceNoteColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(Icons.mic, size: 16, color: AppTheme.voiceNoteColor),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(note.speaker, style: TextStyle(color: AppTheme.voiceNoteColor, fontWeight: FontWeight.w600, fontSize: 14)),
                    TimestampLabel(time: note.unlockTimestamp),
                  ],
                ),
              ),
              if (isFirst) const InterceptedLabel(),
              // Faux play button
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: AppTheme.voiceNoteColor.withOpacity(0.1),
                  shape: BoxShape.circle,
                  border: Border.all(color: AppTheme.voiceNoteColor.withOpacity(0.3)),
                ),
                child: const Icon(Icons.play_arrow, size: 16, color: AppTheme.voiceNoteColor),
              ),
            ],
          ),
          const SizedBox(height: 14),
          // Waveform
          SizedBox(
            height: 28,
            child: Row(
              children: List.generate(40, (i) {
                final h = 5.0 + (i * 11 % 22);
                return Expanded(
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 0.5),
                    height: h,
                    decoration: BoxDecoration(
                      color: (isFirst ? AppTheme.voiceNoteColor : AppTheme.voiceNoteColor.withOpacity(0.35)),
                      borderRadius: BorderRadius.circular(1),
                    ),
                  ),
                );
              }),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            note.transcript,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontStyle: FontStyle.italic,
              height: 1.6,
            ),
          ),
        ],
      ),
    );
  }
}
