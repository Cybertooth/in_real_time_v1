import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/story_item.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';

/// Group chat threads screen — list of intercepted group conversations.
class GroupChatScreen extends ConsumerWidget {
  const GroupChatScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final threadsAsync = ref.watch(groupChatProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('GROUP CHATS')),
      body: threadsAsync.when(
        data: (threads) {
          if (threads.isEmpty) {
            return const EmptyState(
              icon: Icons.group_off,
              title: 'NO THREADS',
              subtitle: 'Intercepted group conversations will appear here.',
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: threads.length,
            itemBuilder: (_, i) => _ThreadCard(thread: threads[i]),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

class _ThreadCard extends StatelessWidget {
  final GroupChatThread thread;
  const _ThreadCard({required this.thread});

  IconData _platformIcon(String p) => switch (p.toLowerCase()) {
    'whatsapp' => Icons.chat,
    'telegram' => Icons.send,
    'imessage' => Icons.message,
    'signal' => Icons.shield,
    _ => Icons.forum,
  };

  @override
  Widget build(BuildContext context) {
    final lastMsg = thread.messages.isNotEmpty ? thread.messages.last : null;
    return GestureDetector(
      onTap: () => _showThread(context),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: AppTheme.cardDecoration(accentBorder: AppTheme.groupChatColor),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                TypeBadge(label: thread.platform, color: AppTheme.groupChatColor, icon: _platformIcon(thread.platform)),
                const Spacer(),
                TimestampLabel(time: thread.unlockTimestamp, showDate: false),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: AppTheme.groupChatColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Icon(Icons.group, color: AppTheme.groupChatColor, size: 18),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(thread.groupName, style: Theme.of(context).textTheme.headlineSmall),
                      Text(
                        '${thread.members.length} members  •  ${thread.messages.length} messages',
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right, color: AppTheme.textMuted, size: 20),
              ],
            ),
            if (lastMsg != null) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: AppTheme.glassDecoration(),
                child: Row(
                  children: [
                    Text('${lastMsg.sender}: ', style: TextStyle(color: AppTheme.groupChatColor, fontWeight: FontWeight.w600, fontSize: 12)),
                    Expanded(
                      child: Text(lastMsg.text, style: Theme.of(context).textTheme.bodySmall, maxLines: 1, overflow: TextOverflow.ellipsis),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showThread(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surfaceLow,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
      ),
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        expand: false,
        builder: (_, scrollCtrl) => _ThreadDetailSheet(thread: thread, scrollController: scrollCtrl),
      ),
    );
  }
}

class _ThreadDetailSheet extends StatelessWidget {
  final GroupChatThread thread;
  final ScrollController scrollController;
  const _ThreadDetailSheet({required this.thread, required this.scrollController});

  // Assign a consistent colour per sender name
  static const _senderColors = [
    AppTheme.accentNeon,
    AppTheme.tertiary,
    AppTheme.voiceNoteColor,
    AppTheme.socialPostColor,
    AppTheme.emailColor,
    AppTheme.groupChatColor,
    AppTheme.alertAmber,
  ];

  Color _colorFor(String sender) {
    final idx = sender.hashCode.abs() % _senderColors.length;
    return _senderColors[idx];
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
              const Icon(Icons.group, color: AppTheme.groupChatColor, size: 22),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      thread.groupName,
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    Text(
                      '${thread.platform.toUpperCase()}  •  ${thread.members.length} members',
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                  ],
                ),
              ),
              const InterceptedLabel(),
            ],
          ),
          const SizedBox(height: 8),
          // Member chips
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: thread.members.map((m) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _colorFor(m).withOpacity(0.08),
                  borderRadius: BorderRadius.circular(3),
                ),
                child: Text(m, style: TextStyle(color: _colorFor(m), fontSize: 11, fontWeight: FontWeight.w500)),
              );
            }).toList(),
          ),
          const SizedBox(height: 24),
          // Messages
          ...thread.messages.map((msg) {
            final color = _colorFor(msg.sender);
            return Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(msg.sender, style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 12)),
                  const SizedBox(height: 2),
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.04),
                      borderRadius: const BorderRadius.only(
                        topRight: Radius.circular(8),
                        bottomLeft: Radius.circular(8),
                        bottomRight: Radius.circular(8),
                      ),
                      border: Border.all(color: color.withOpacity(0.08)),
                    ),
                    child: Text(msg.text, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.5)),
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
