import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../models/story_item.dart';
import '../widgets/shared_widgets.dart';

class ChatScreen extends ConsumerWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chatsAsync = ref.watch(chatProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('CHATS')),
      body: chatsAsync.when(
        data: (chats) {
          if (chats.isEmpty) {
            return const EmptyState(
              icon: Icons.chat_bubble_outline,
              title: 'NO MESSAGES',
              subtitle: 'Intercepted messages will appear here.',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: chats.length,
            itemBuilder: (context, index) => _buildChatBubble(context, chats[index]),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildChatBubble(BuildContext context, Chat chat) {
    final isMe = chat.isProtagonist;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          if (!isMe)
            Padding(
              padding: const EdgeInsets.only(left: 8, bottom: 3),
              child: Text(
                chat.senderId,
                style: TextStyle(color: AppTheme.chatColor, fontSize: 11, fontWeight: FontWeight.w600),
              ),
            ),
          Container(
            padding: const EdgeInsets.all(12),
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.72),
            decoration: BoxDecoration(
              color: isMe ? AppTheme.accentNeon.withOpacity(0.08) : AppTheme.surface,
              border: Border.all(
                color: isMe ? AppTheme.accentNeon.withOpacity(0.2) : Colors.white.withOpacity(0.06),
              ),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(8),
                topRight: const Radius.circular(8),
                bottomLeft: isMe ? const Radius.circular(8) : Radius.zero,
                bottomRight: isMe ? Radius.zero : const Radius.circular(8),
              ),
            ),
            child: Text(
              chat.text,
              style: TextStyle(
                color: isMe ? AppTheme.accentSoft : AppTheme.textBody,
                height: 1.4,
              ),
            ),
          ),
          Padding(
            padding: EdgeInsets.only(top: 2, left: isMe ? 0 : 8, right: isMe ? 8 : 0),
            child: TimestampLabel(time: chat.unlockTimestamp, showDate: false),
          ),
        ],
      ),
    );
  }
}
