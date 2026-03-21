import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';
import 'chat_thread_screen.dart';

class ConversationsScreen extends ConsumerWidget {
  const ConversationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final threadsAsync = ref.watch(conversationsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('MESSAGES')),
      body: threadsAsync.when(
        data: (threads) {
          if (threads.isEmpty) {
            return const EmptyState(
              icon: Icons.chat_bubble_outline,
              title: 'NO CONVERSATIONS',
              subtitle: 'Encrypted message threads will appear here.',
            );
          }

          return ListView.separated(
            padding: const EdgeInsets.symmetric(vertical: 8),
            itemCount: threads.length,
            separatorBuilder: (context, index) => Divider(color: Colors.white.withOpacity(0.04), indent: 72),
            itemBuilder: (context, index) {
              final thread = threads[index];
              return _ConversationTile(thread: thread);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }
}

class _ConversationTile extends StatelessWidget {
  final ConversationThread thread;
  const _ConversationTile({required this.thread});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ChatThreadScreen(
              conversationId: thread.id,
              title: thread.title,
              isGroup: thread.isGroup,
            ),
          ),
        );
      },
      leading: CircleAvatar(
        backgroundColor: thread.isGroup 
            ? AppTheme.groupChatColor.withOpacity(0.1) 
            : AppTheme.chatColor.withOpacity(0.1),
        child: Icon(
          thread.isGroup ? Icons.group : Icons.person,
          color: thread.isGroup ? AppTheme.groupChatColor : AppTheme.chatColor,
        ),
      ),
      title: Text(thread.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
      subtitle: Text(
        thread.lastMessage,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(color: AppTheme.textDim, fontSize: 13),
      ),
      trailing: Text(
        _formatTime(thread.lastTimestamp),
        style: const TextStyle(color: AppTheme.textMuted, fontSize: 11),
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final now = DateTime.now();
    if (dt.day == now.day && dt.month == now.month && dt.year == now.year) {
      return '${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
    }
    return '${dt.month}/${dt.day}';
  }
}
